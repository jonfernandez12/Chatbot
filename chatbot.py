import os
import dialogflow
import logging
import requests
import json
import psql
from google.api_core.exceptions import InvalidArgument
from sqlalchemy.sql import select 
from models import Film, User, Recomendation
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

intents=[]
string = 'notPopular'
string3 = 'Popular'
string2 = 'Genre'

def getQueryValues(intents):
    values = []
    print(type(intents))
    print(intents[-1])
    intent = intents[-1]
    intent = intent.split("-")
    for i in intents:
        if string2 in i:
            genre = i.split("-")
            startdate = intent[0]
            enddate = intent[1]
            values.append(genre[1].replace(" ",""))
            values.append(startdate)
            values.append(enddate)
            return values
    
def getRespuesta(query):
    print(query)
    respuesta = ("Título: "+query.title+"\n"+
                "Fecha:"+query.year+"\n"+
                "Resumen: "+query.plot+"\n"+
                "Link: "+query.link)
    return respuesta

def getQuery(db_session,intents):
    values = getQueryValues(intents)
    s=db_session.query(Film).filter(Film.genre.ilike('%'+values[0]+'%')).filter(Film.year <= values[2]).filter(Film.year >= values[1]).order_by(Film.rating.asc()).first()
    print(s)
    return s


def echo(update, context):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = '/home/jon/Documents/Chatbot/Chatbot/private_key.json'

    DIALOGFLOW_PROJECT_ID = 'jonbot-sqoh'
    DIALOGFLOW_LANGUAGE_CODE = 'es'
    SESSION_ID = 'me'

    text_to_be_analyzed = update.message.text
    user=update.message.from_user
    db_session = psql.getConnection()
    psql.upsertUsers(db_session,user)
    db_session.close()

    #Dialog Flow cliente
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(DIALOGFLOW_PROJECT_ID, SESSION_ID)
    text_input = dialogflow.types.TextInput(text=text_to_be_analyzed, language_code=DIALOGFLOW_LANGUAGE_CODE)
    query_input = dialogflow.types.QueryInput(text=text_input)

    try:
        response = session_client.detect_intent(session=session, query_input=query_input)
    except InvalidArgument:
        raise

    print("Query text:", response.query_result.query_text)
    print("Detected intent:", response.query_result.intent.display_name)
    print("Detected intent confidence:", response.query_result.intent_detection_confidence)
    print("Fulfillment text:", response.query_result.fulfillment_text)
    
    intent = response.query_result.intent.display_name
    intents.append(intent)


    if (intent=="Hola"):
        update.message.reply_text('¡Hola '+user["first_name"]+"! "+response.query_result.fulfillment_text)

    if (string in intent):#No populare
        s=getQuery(db_session, intents)
        respuesta = getRespuesta(s)
        response.query_result.fulfillment_text=respuesta
    elif (string3 in intent):#populare
        s=getQuery(db_session,intents)
        respuesta = getRespuesta(s)
        response.query_result.fulfillment_text=respuesta
    
    #db_session = psql.getConnection()
    #s=db_session.query(Film).filter(Film.genre.ilike(intent+'%')).first()


    #response.query_result.fulfillment_text = respuesta
    update.message.reply_text(response.query_result.fulfillment_text)
    #newRec = Recomendation(id,s.title,s.filmId)
    #db_session.insertRecomendation(newRec)
    #db_session.close()


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater("1544255841:AAG6oD1w09XqS5e5pTMfIfjkr1c6bkF5ddA", use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    
    # on different commands - answer in Telegram
    #dp.add_handler(CommandHandler("start", start))

    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    dp.add_handler(echo_handler)
    # on noncommand i.e message - echo the message on Telegram
    #dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    #dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()



if __name__ == '__main__':
    main()
    