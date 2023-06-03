from fastapi import Request, Response
import app.main as main

def MesseageQueueWrapper(channel, basic_deliver, properties, body):
    """
    ESTE TEXTO NO LO ESCRIBI YO!!! MI INGLES NO ESTAN BUENO XD
    DEJO EL TEXTO ORIGINAL PARA QUE SE SEPA QUÉ RECIBE/HACE ESTA FUNCION
    O SEA... "MesseageQueueWrapper" ES UN WRAPPER DE LA FUNCION "on_message()" 
    del ConsumerQueue.
    
    
    Invoked by pika when a message is delivered from RabbitMQ. The
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
    
    # en BODY esta lo que se envia desde los microservicios (Serian los productores!)
    
    main.logger.info('Received message # %s from %s: %s',
                basic_deliver.delivery_tag, properties.app_id, body)
    
    
    # ACA METER LA LOGICA DE LO QUE SE QUIERE HACER CON EL MENSAJE QUE SE RECIBE
    # GUARDAR EN POSTGRESQL!
    # ATECIÓN!:
    # OJOOOOOOOOOOOOOOO CON QUE EL SAVE EN POSTGREA SEA ASYNC!! SINO TRABAMOS EL EVENT LOOP
    # O PEOR.... SI JUSTO TARDA MUCHO EN GAURDAR UN DATO EN POSTGRESQL, SE TRABARA EL EVENT LOOP 
    # Y NO SE VAN A PODER PROCESAR LOS MENSAJES QUE SE VAN RECIBIENDO
    # ..
    # ..
    # o sea, busco evitar lo que nos paso con la libreria que era sincronica !!!! "import request"
    # esa libreria era sincronica y trababa el event loop, por eso no podiamos procesar los requests
    # que se enviaban del servicio "A -> B -> A" porque en "A" se trababa el event loop por esperar 
    # una respuesta con una libreria que lo hacia sincronico!!!!!
