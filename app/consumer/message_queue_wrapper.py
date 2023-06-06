import json
from fastapi import Request, Response
import app.main as main

async def MesseageQueueWrapper(channel, basic_deliver, properties, message):
    """
    Wrapper de la funcion "ConsumerQueue.on_message()" 

    :param pika.channel.Channel channel: The channel object
    :param pika.Spec.Basic.Deliver: basic_deliver method
    :param pika.Spec.BasicProperties: properties
    :param bytes body: The message body
    """
    
    message = json.loads(message.decode('utf-8'))
    main.logger.info(f"MESSAGE RECEIVED: {message}")
    
    
    # ACA METER LA LOGICA DE LO QUE SE QUIERE HACER CON EL MENSAJE QUE SE RECIBE
    # GUARDAR EN POSTGRESQL!!
    # pensar bien que guardar.. conviene guardar cada requests? apareceran millones de rows
    # o quizas conviene guardar ciertos requests... o los que piden
    # o guardar.. tal requests se hizo tantas veces en tal dia .. o tal requests se ejecuto tantas veces
    # o tal requests devolvio tal status code tantas veces
    # es pa pensar! y definir bien que metrics mostrar en backoffice en base a lo que se guarda!