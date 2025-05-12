import requests
import logging
from telegram import Update
from telegram.ext import (
    filters,
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler, ConversationHandler)

QUESTION_START = range(1)

async def handlerQuestionStart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    handles /question command
    """
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Type /FAQ to view our frequently asked questions, or type your question and our sellers will answer them accordingly"
    )
    return QUESTION_START

async def handlerQuestionShowFAQ(update:Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    shows FAQs
    """
    await context.bot.send_message(
        chat_id = update.effective_chat.id,
        text="Please visit the link below for the FAQ!\n" +
             "https://docs.google.com/document/d/1v4ofc_tfiPyNuJWW-iOHLFUolAb5srZfnWqnke90Qlk/edit?tab=t.vhga5eeqazd4"
    )
    return ConversationHandler.END

async def handlerQuestionAskSeller(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    forwards the question to the sellers
    """
    await context.bot.forward_message (
        chat_id=update.effective_chat.id, #replace with seller's telegram id
        from_chat_id=update.effective_chat.id,
        message_id=update.message.message_id
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Your message has been forwarded to our sellers! A reply will be given in 24 business hours"
    )
    return ConversationHandler.END

async def handlerQuestionFallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    fallback function in case exception occurs
    """
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Exiting Q&A mode"
    )
    return ConversationHandler.END