import functools
import os
import time
import pika
from app.consumer.message_queue_wrapper import MesseageQueueWrapper
import app.main as main

from pika.adapters.asyncio_connection import AsyncioConnection


class ConsumerQueue(object):
    """This is an example consumer that will handle unexpected interactions
    with RabbitMQ such as channel and connection closures.

    If RabbitMQ closes the connection, this class will stop and indicate
    that reconnection is necessary. You should look at the output, as
    there are limited reasons why the connection may be closed, which
    usually are tied to permission related issues or socket timeouts.

    If the channel is closed, it will indicate a problem with one of the
    commands that were issued and that should surface in the output as well.

    """
    instance = None # For Singleton pattern!

    EXCHANGE = "get_me_hired_exchange"
    EXCHANGE_TYPE = "direct"
    QUEUE = "get_me_hired_queue"
    ROUTING_KEY = "jobs_search"
    
    def __new__(cls,  amqp_url):
        """Create a new instance of the consumer class, passing in the AMQP
        URL used to connect to RabbitMQ.

        :param str amqp_url: The AMQP url to connect with

        """
        if cls.instance is None:
            cls.instance = super().__new__(cls)
            cls.instance.should_reconnect = False
            cls.instance.was_consuming = False

            cls.instance._connection = None
            cls.instance._channel = None
            cls.instance._closing = False
            cls.instance._consumer_tag = None
            cls.instance._url = amqp_url
            cls.instance._consuming = False
            # In production, experiment with higher prefetch values
            # for higher consumer throughput
            cls.instance._prefetch_count = 1
        return cls.instance
    
    def connect(cls):
        """This method connects to RabbitMQ, returning the connection handle.
        When the connection is established, the on_connection_open method
        will be invoked by pika.

        :rtype: pika.adapters.asyncio_connection.AsyncioConnection

        """
        main.logger.info('Connecting to %s', cls.instance._url)
        return AsyncioConnection(
            parameters=pika.URLParameters(cls.instance._url),
            on_open_callback=cls.instance.on_connection_open,
            on_open_error_callback=cls.instance.on_connection_open_error,
            on_close_callback=cls.instance.on_connection_closed)

    def close_connection(cls):
        cls.instance._consuming = False
        if cls.instance._connection.is_closing or cls.instance._connection.is_closed:
            main.logger.info('Connection is closing or already closed')
        else:
            main.logger.info('Closing connection')
            cls.instance._connection.close()

    def on_connection_open(cls, _unused_connection):
        """This method is called by pika once the connection to RabbitMQ has
        been established. It passes the handle to the connection object in
        case we need it, but in this case, we'll just mark it unused.

        :param pika.adapters.asyncio_connection.AsyncioConnection _unused_connection:
           The connection

        """
        main.logger.info('Connection opened')
        cls.instance.open_channel()

    def on_connection_open_error(cls, _unused_connection, err):
        """This method is called by pika if the connection to RabbitMQ
        can't be established.

        :param pika.adapters.asyncio_connection.AsyncioConnection _unused_connection:
           The connection
        :param Exception err: The error

        """
        main.logger.error('Connection open failed: %s', err)
        cls.instance.reconnect()

    def on_connection_closed(cls, _unused_connection, reason):
        """This method is invoked by pika when the connection to RabbitMQ is
        closed unexpectedly. Since it is unexpected, we will reconnect to
        RabbitMQ if it disconnects.

        :param pika.connection.Connection connection: The closed connection obj
        :param Exception reason: exception representing reason for loss of
            connection.

        """
        cls.instance._channel = None
        if cls.instance._closing:
            cls.instance._connection.ioloop.stop()
        else:
            main.logger.warning('Connection closed, reconnect necessary: %s', reason)
            cls.instance.reconnect()

    def reconnect(cls):
        """Will be invoked if the connection can't be opened or is
        closed. Indicates that a reconnect is necessary then stops the
        ioloop.

        """
        cls.instance.should_reconnect = True
        cls.instance.stop()

    def open_channel(cls):
        """Open a new channel with RabbitMQ by issuing the Channel.Open RPC
        command. When RabbitMQ responds that the channel is open, the
        on_channel_open callback will be invoked by pika.

        """
        main.logger.info('Creating a new channel')
        cls.instance._connection.channel(on_open_callback=cls.instance.on_channel_open)

    def on_channel_open(cls, channel):
        """This method is invoked by pika when the channel has been opened.
        The channel object is passed in so we can make use of it.

        Since the channel is now open, we'll declare the exchange to use.

        :param pika.channel.Channel channel: The channel object

        """
        main.logger.info('Channel opened')
        cls.instance._channel = channel
        cls.instance.add_on_channel_close_callback()
        cls.instance.setup_exchange(cls.instance.EXCHANGE)

    def add_on_channel_close_callback(cls):
        """This method tells pika to call the on_channel_closed method if
        RabbitMQ unexpectedly closes the channel.

        """
        main.logger.info('Adding channel close callback')
        cls.instance._channel.add_on_close_callback(cls.instance.on_channel_closed)

    def on_channel_closed(cls, channel, reason):
        """Invoked by pika when RabbitMQ unexpectedly closes the channel.
        Channels are usually closed if you attempt to do something that
        violates the protocol, such as re-declare an exchange or queue with
        different parameters. In this case, we'll close the connection
        to shutdown the object.

        :param pika.channel.Channel: The closed channel
        :param Exception reason: why the channel was closed

        """
        main.logger.warning('Channel %i was closed: %s', channel, reason)
        cls.instance.close_connection()

    def setup_exchange(cls, exchange_name):
        """Setup the exchange on RabbitMQ by invoking the Exchange.Declare RPC
        command. When it is complete, the on_exchange_declareok method will
        be invoked by pika.

        :param str|unicode exchange_name: The name of the exchange to declare

        """
        main.logger.info('Declaring exchange: %s', exchange_name)
        # Note: using functools.partial is not required, it is demonstrating
        # how arbitrary data can be passed to the callback when it is called
        cb = functools.partial(
            cls.instance.on_exchange_declareok, userdata=exchange_name)
        cls.instance._channel.exchange_declare(
            exchange=exchange_name,
            exchange_type=cls.instance.EXCHANGE_TYPE,
            callback=cb)

    def on_exchange_declareok(cls, _unused_frame, userdata):
        """Invoked by pika when RabbitMQ has finished the Exchange.Declare RPC
        command.

        :param pika.Frame.Method unused_frame: Exchange.DeclareOk response frame
        :param str|unicode userdata: Extra user data (exchange name)

        """
        main.logger.info('Exchange declared: %s', userdata)
        cls.instance.setup_queue(cls.instance.QUEUE)

    def setup_queue(cls, queue_name):
        """Setup the queue on RabbitMQ by invoking the Queue.Declare RPC
        command. When it is complete, the on_queue_declareok method will
        be invoked by pika.

        :param str|unicode queue_name: The name of the queue to declare.

        """
        main.logger.info('Declaring queue %s', queue_name)
        cb = functools.partial(cls.instance.on_queue_declareok, userdata=queue_name)
        cls.instance._channel.queue_declare(queue=queue_name, callback=cb)

    def on_queue_declareok(cls, _unused_frame, userdata):
        """Method invoked by pika when the Queue.Declare RPC call made in
        setup_queue has completed. In this method we will bind the queue
        and exchange together with the routing key by issuing the Queue.Bind
        RPC command. When this command is complete, the on_bindok method will
        be invoked by pika.

        :param pika.frame.Method _unused_frame: The Queue.DeclareOk frame
        :param str|unicode userdata: Extra user data (queue name)

        """
        queue_name = userdata
        main.logger.info('Binding %s to %s with %s', cls.instance.EXCHANGE, queue_name,
                    cls.instance.ROUTING_KEY)
        cb = functools.partial(cls.instance.on_bindok, userdata=queue_name)
        cls.instance._channel.queue_bind(
            queue_name,
            cls.instance.EXCHANGE,
            routing_key=cls.instance.ROUTING_KEY,
            callback=cb)

    def on_bindok(cls, _unused_frame, userdata):
        """Invoked by pika when the Queue.Bind method has completed. At this
        point we will set the prefetch count for the channel.

        :param pika.frame.Method _unused_frame: The Queue.BindOk response frame
        :param str|unicode userdata: Extra user data (queue name)

        """
        main.logger.info('Queue bound: %s', userdata)
        cls.instance.set_qos()

    def set_qos(cls):
        """This method sets up the consumer prefetch to only be delivered
        one message at a time. The consumer must acknowledge this message
        before RabbitMQ will deliver another one. You should experiment
        with different prefetch values to achieve desired performance.

        """
        cls.instance._channel.basic_qos(
            prefetch_count=cls.instance._prefetch_count, callback=cls.instance.on_basic_qos_ok)

    def on_basic_qos_ok(cls, _unused_frame):
        """Invoked by pika when the Basic.QoS method has completed. At this
        point we will start consuming messages by calling start_consuming
        which will invoke the needed RPC commands to start the process.

        :param pika.frame.Method _unused_frame: The Basic.QosOk response frame

        """
        main.logger.info('QOS set to: %d', cls.instance._prefetch_count)
        cls.instance.start_consuming()

    def start_consuming(cls):
        """This method sets up the consumer by first calling
        add_on_cancel_callback so that the object is notified if RabbitMQ
        cancels the consumer. It then issues the Basic.Consume RPC command
        which returns the consumer tag that is used to uniquely identify the
        consumer with RabbitMQ. We keep the value to use it when we want to
        cancel consuming. The "on_message" method is passed in as a callback pika
        will invoke when a message is fully received.

        """
        main.logger.info('Issuing consumer related RPC commands')
        cls.instance.add_on_cancel_callback()
        cls.instance._consumer_tag = cls.instance._channel.basic_consume(
            cls.instance.QUEUE, cls.instance.on_message)
        cls.instance.was_consuming = True
        cls.instance._consuming = True

    def add_on_cancel_callback(cls):
        """Add a callback that will be invoked if RabbitMQ cancels the consumer
        for some reason. If RabbitMQ does cancel the consumer,
        on_consumer_cancelled will be invoked by pika.

        """
        main.logger.info('Adding consumer cancellation callback')
        cls.instance._channel.add_on_cancel_callback(cls.instance.on_consumer_cancelled)

    def on_consumer_cancelled(cls, method_frame):
        """Invoked by pika when RabbitMQ sends a Basic.Cancel for a consumer
        receiving messages.

        :param pika.frame.Method method_frame: The Basic.Cancel frame

        """
        main.logger.info('Consumer was cancelled remotely, shutting down: %r',
                    method_frame)
        if cls.instance._channel:
            cls.instance._channel.close()

    def on_message(cls, channel, basic_deliver, properties, body):
        """Invoked by pika when a message is delivered from RabbitMQ. The
        channel is passed for your convenience. The basic_deliver object that
        is passed in carries the exchange, routing key, delivery tag and
        a redelivered flag for the message. The properties passed in is an
        instance of BasicProperties with the message properties and the body
        is the message that was sent.

        :param pika.channel.Channel channel: The channel object
        :param pika.Spec.Basic.Deliver: basic_deliver method
        :param pika.Spec.BasicProperties: properties
        :param bytes body: The message body

        """
        MesseageQueueWrapper(channel, basic_deliver, properties, body)
        
        # !TODO ni idea para que son los ACK en esto, pero por las dudas..
        cls.instance.acknowledge_message(basic_deliver.delivery_tag) 
        
    def acknowledge_message(cls, delivery_tag):
        """Acknowledge the message delivery from RabbitMQ by sending a
        Basic.Ack RPC method for the delivery tag.

        :param int delivery_tag: The delivery tag from the Basic.Deliver frame

        """
        main.logger.info('Acknowledging message %s', delivery_tag)
        cls.instance._channel.basic_ack(delivery_tag)

    def stop_consuming(cls):
        """Tell RabbitMQ that you would like to stop consuming by sending the
        Basic.Cancel RPC command.

        """
        if cls.instance._channel:
            main.logger.info('Sending a Basic.Cancel RPC command to RabbitMQ')
            cb = functools.partial(
                cls.instance.on_cancelok, userdata=cls.instance._consumer_tag)
            cls.instance._channel.basic_cancel(cls.instance._consumer_tag, cb)

    def on_cancelok(cls, _unused_frame, userdata):
        """This method is invoked by pika when RabbitMQ acknowledges the
        cancellation of a consumer. At this point we will close the channel.
        This will invoke the on_channel_closed method once the channel has been
        closed, which will in-turn close the connection.

        :param pika.frame.Method _unused_frame: The Basic.CancelOk frame
        :param str|unicode userdata: Extra user data (consumer tag)

        """
        cls.instance._consuming = False
        main.logger.info(
            'RabbitMQ acknowledged the cancellation of the consumer: %s',
            userdata)
        cls.instance.close_channel()

    def close_channel(cls):
        """Call to close the channel with RabbitMQ cleanly by issuing the
        Channel.Close RPC command.

        """
        main.logger.info('Closing the channel')
        cls.instance._channel.close()

    def run(cls):
        """Run the example consumer by connecting to RabbitMQ and then
        starting the IOLoop to block and allow the AsyncioConnection to operate.

        """
        cls.instance._connection = cls.instance.connect()
        cls.instance._connection.ioloop.run_forever()

    def stop(cls):
        """Cleanly shutdown the connection to RabbitMQ by stopping the consumer
        with RabbitMQ. When RabbitMQ confirms the cancellation, on_cancelok
        will be invoked by pika, which will then closing the channel and
        connection. The IOLoop is started again because this method is invoked
        when CTRL-C is pressed raising a KeyboardInterrupt exception. This
        exception stops the IOLoop which needs to be running for pika to
        communicate with RabbitMQ. All of the commands issued prior to starting
        the IOLoop will be buffered but not processed.

        """
        if not cls.instance._closing:
            cls.instance._closing = True
            main.logger.info('Stopping')
            if cls.instance._consuming:
                cls.instance.stop_consuming()
                cls.instance._connection.ioloop.run_forever()
            else:
                cls.instance._connection.ioloop.stop()
            main.logger.info('Stopped')


def getConsumerQueue() -> ConsumerQueue:
    return ConsumerQueue(os.environ["CLOUDAMQP_URL"])

async def runConsumerQueue():
    getConsumerQueue().run()


# !TODO INTERESANTE PARA RECONECCION.. NO LO VI .. HABRIA QUE CAMBIAR EL SINGLETON :S
# class ReconnectingExampleConsumer(object):
#     """This is an example consumer that will reconnect if the nested
#     ExampleConsumer indicates that a reconnect is necessary.

#     """

#     def __init__(cls.instance, amqp_url):
#         cls.instance._reconnect_delay = 0
#         cls.instance._amqp_url = amqp_url
#         cls.instance._consumer = ConsumerQueue(cls.instance._amqp_url)

#     def run(cls.instance):
#         while True:
#             try:
#                 main.logger.info('Starting cls.instance._consumer.run()')
#                 cls.instance._consumer.run()
#             except KeyboardInterrupt:
#                 main.logger.info('Stopping cls.instance._consumer.stop()')
#                 cls.instance._consumer.stop()
#                 break
#             main.logger.info('Maybe reconnecting cls.instance._maybe_reconnect()')
#             cls.instance._maybe_reconnect()

#     def _maybe_reconnect(cls.instance):
#         if cls.instance._consumer.should_reconnect:
#             cls.instance._consumer.stop()
#             reconnect_delay = cls.instance._get_reconnect_delay()
#             main.logger.info('Reconnecting after %d seconds', reconnect_delay)
#             time.sleep(reconnect_delay)
#             cls.instance._consumer = ConsumerQueue(cls.instance._amqp_url)

#     def _get_reconnect_delay(cls.instance):
#         if cls.instance._consumer.was_consuming:
#             cls.instance._reconnect_delay = 0
#         else:
#             cls.instance._reconnect_delay += 1
#         if cls.instance._reconnect_delay > 30:
#             cls.instance._reconnect_delay = 30
#         return cls.instance._reconnect_delay


# def main():
#     logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
#     amqp_url = 'amqp://guest:guest@localhost:5672/%2F'
#     consumer = ReconnectingExampleConsumer(amqp_url)
#     consumer.run()


# if __name__ == '__main__':
    # main()