import os
import logging
import asyncio
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Enable detailed logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('.env')

# Get bot token
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN or TOKEN == 'your_bot_token_here':
    logger.error('No valid bot token found in .env file')
    exit(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    logger.info(f"Start command received from {update.effective_user.id}")
    try:
        await update.message.reply_text('Welcome to the group! I am your welcome bot.')
    except Exception as e:
        logger.error(f"Error in start command: {e}")

async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when a new member joins the group."""
    logger.info(f"New member(s) joined: {update.message.new_chat_members}")
    
    if not update.message.new_chat_members:
        logger.warning("No new members found in the update")
        return
        
    for member in update.message.new_chat_members:
        try:
            # Check if the new member is the bot itself
            if member.is_bot and member.id == context.bot.id:
                logger.info("Bot was added to a new group")
                await update.message.reply_text(
                    "🤖 Thanks for adding me! I'll welcome new members to this group. "
                    "Make me an admin to get the best experience! 🚀"
                )
                return
            
            # Get member count for fun stats
            chat_member_count = await context.bot.get_chat_member_count(update.effective_chat.id)
            
            # Random emoji for variety
            import random
            emojis = ["👋", "🎉", "🌟", "✨", "🙌", "🤗", "😊", "🎊", "👏", "💫"]
            welcome_emoji = random.choice(emojis)
            
            # Different welcome messages for variety
            welcome_messages = [
                f"{welcome_emoji} *Welcome* {member.mention_markdown_v2()} to *{update.effective_chat.title}*! {welcome_emoji}\n"
                f"You're member #{chat_member_count}! 🎯",
                
                f"{welcome_emoji} *Welcome* {member.mention_markdown_v2()}! {welcome_emoji}\n"
                f"We're now *{chat_member_count}* members strong! 💪",
                
                f"{welcome_emoji} *Welcome* {member.mention_markdown_v2()}! {welcome_emoji}\n"
                f"Enjoy your stay in *{update.effective_chat.title}*! 🏡",
                
                f"{welcome_emoji} *Welcome* {member.mention_markdown_v2()}! {welcome_emoji}\n"
                f"Don't forget to check out the group rules! 📜"
            ]
            
            # Get user profile photo if available
            try:
                photos = await context.bot.get_user_profile_photos(member.id, limit=1)
                has_photo = bool(photos.photos)
            except Exception as e:
                logger.warning(f"Couldn't get profile photo: {e}")
                has_photo = False
            
            # Custom message based on whether user has profile photo
            if has_photo:
                welcome_messages.append(
                    f"{welcome_emoji} *Welcome* {member.mention_markdown_v2()}! {welcome_emoji}\n"
                    f"Love your profile picture! 😍"
                )
            
            # Randomly select a welcome message
            welcome_message = random.choice(welcome_messages)
            
            # Add some footer text
            welcome_message += "\n\n_Type /help to see what I can do!"
            
            # Send the welcome message
            await update.message.reply_text(
                welcome_message,
                parse_mode='MarkdownV2',
                disable_web_page_preview=True
            )
            
            # Send a fun sticker (optional)
            stickers = [
                'CAACAgIAAxkBAAELVf5mB2h2Z2X2Z2ZmZmZmZmZmZmZmZgACAgADwDZPE_lqX5qCaCaeNAQ',  # 👋 wave
                'CAACAgIAAxkBAAELVgBmB2iBZ2X2Z2ZmZmZmZmZmZmZmZgACAwADwDZPE1mWbkw5XzQlNAQ',  # 🎉 tada
                'CAACAgIAAxkBAAELVgJmB2iJZ2X2Z2ZmZmZmZmZmZmZmZgACBAADwDZPE1mWbkw5XzQlNAQ'   # 🎊 confetti
            ]
            try:
                await context.bot.send_sticker(
                    chat_id=update.effective_chat.id,
                    sticker=random.choice(stickers),
                    reply_to_message_id=update.message.message_id
                )
            except Exception as e:
                logger.warning(f"Couldn't send sticker: {e}")
                
        except Exception as e:
            logger.error(f"Error in new_member: {e}")
            try:
                # Fallback simple welcome
                await update.message.reply_text(
                    f"👋 Welcome to the group, {member.mention_markdown_v2()}! 🎉",
                    parse_mode='MarkdownV2'
                )
            except Exception as fallback_error:
                logger.error(f"Fallback welcome failed: {fallback_error}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by Updates."""
    logger.error(f"Error while processing update: {update}", exc_info=context.error)

def main():
    """Start the bot."""
    import asyncio
    
    # Create event loop explicitly for Python 3.11+
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    async def run_bot():
        """Run the bot with proper async context."""
        try:
            logger.info("Initializing bot...")
            
            # Create the Application
            application = Application.builder().token(TOKEN).build()
            logger.info("Application created successfully")
            
            # Add handlers
            application.add_handler(CommandHandler("start", start))
            application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))
            
            # Add error handler
            application.add_error_handler(error_handler)
            
            # Get bot info
            try:
                bot_info = await application.bot.get_me()
                logger.info(f"Bot @{bot_info.username} is starting...")
                logger.info(f"Bot ID: {bot_info.id}, Name: {bot_info.full_name}")
            except Exception as e:
                logger.error(f"Failed to get bot info: {e}")
                return
            
            # Start the Bot
            logger.info("Bot is running. Press Ctrl+C to stop.")
            await application.initialize()
            await application.start()
            await application.updater.start_polling()
            
            # Keep the application running until interrupted
            while True:
                await asyncio.sleep(1)
                
            # This will never be reached, but it's good practice to have cleanup
            await application.updater.stop()
            await application.stop()
            
        except Exception as e:
            logger.critical(f"Failed to start bot: {e}")
            raise
    
    try:
        loop.run_until_complete(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        loop.close()

if __name__ == '__main__':
    main()
