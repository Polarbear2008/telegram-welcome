import os
import logging
import random
import json
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('.env')

# In-memory storage for active members (in a real app, use a database)
active_members = defaultdict(lambda: {'messages': 0, 'last_active': None, 'username': None, 'full_name': None})
weekly_stats = defaultdict(int)
monthly_stats = defaultdict(int)
last_weekly_reset = datetime.now()
last_monthly_reset = datetime.now()

# Sticker set names from popular Telegram sticker packs
STICKER_SETS = [
    'MemeFun',  # Funny memes
    'FunnyPanda',  # Cute panda stickers
    'CuteAnimals',  # Cute animal stickers
]

# Fallback sticker file IDs if sticker sets fail
# These are common sticker file IDs that should work in most cases
FALLBACK_STICKERS = [
    'CAACAgIAAxkBAAIBOmYHcYVgAAH2lLpV5XKJZ2X2Z2ZmZmYAAgIAA8A2TxNZlm5MOV80JTQE',  # smiley
    'CAACAgIAAxkBAAIBPGYHcYVgAAH4lLpV5XKJZ2X2Z2ZmZmYAAgQAA8A2TxNZlm5MOV80JTQE',  # tada
    'CAACAgIAAxkBAAIBPmYHcYVgAAH5lLpV5XKJZ2X2Z2ZmZmYAAgUAA8A2TxNZlm5MOV80JTQE',  # confetti
    'CAACAgIAAxkBAAIBQGYHcYVgAAH6lLpV5XKJZ2X2Z2ZmZmYAAgYAA8A2TxNZlm5MOV80JTQE',  # balloon
    'CAACAgIAAxkBAAIBQmYHcYVgAAH7lLpV5XKJZ2X2Z2ZmZmYAAgcAA8A2TxNZlm5MOV80JTQE',   # trophy
    'CAACAgQAAxkBAAIBRGYHcYVgAAH8lLpV5XKJZ2X2Z2ZmZmYAAhAAAwEAA1KNYjFjW6s7vzQlNAQ',  # thumbs up
    'CAACAgIAAxkBAAIBRmYHcYVgAAH9lLpV5XKJZ2X2Z2ZmZmYAAhEAA8A2TxNZlm5MOV80JTQE',   # face with tears of joy
    'CAACAgIAAxkBAAIBSGYHcYVgAAH-lLpV5XKJZ2X2Z2ZmZmYAAhIAA8A2TxNZlm5MOV80JTQE',   # red heart
    'CAACAgIAAxkBAAIBSmYHcYVgAAH_lLpV5XKJZ2X2Z2ZmZmYAAhMAA8A2TxNZlm5MOV80JTQE',   # smiling face with heart-eyes
    'CAACAgIAAxkBAAIBTGYHcYVgAAEAlbpV5XKJZ2X2Z2ZmZmYAAhQAA8A2TxNZlm5MOV80JTQE'    # direct hit
]

# Jokes database
JOKES = [
    "Why don't scientists trust atoms? Because they make up everything!",
    "I'm not arguing, I'm just explaining why I'm right.",
    "I told my wife she was drawing her eyebrows too high. She looked surprised.",
    "Parallel lines have so much in common… it's a shame they'll never meet.",
    "I threw a boomerang a few years ago. I now live in constant fear.",
    "Why don't skeletons fight each other? They don't have the guts.",
    "My boss told me to have a good day… so I went home.",
    "I told my computer I needed a break, and now it won't stop sending me beach wallpapers.",
    "Why did the scarecrow win an award? Because he was outstanding in his field.",
    "I'm not lazy, I'm just on energy-saving mode.",
    "Why do cows wear bells? Because their horns don't work.",
    "Why can't your nose be 12 inches long? Because then it would be a foot.",
    "I used to play piano by ear, but now I use my hands.",
    "I have a split personality, said Tom, being Frank.",
    "Don't trust atoms. They make up everything.",
    "If I had a dollar for every time I got distracted… I wish I had a puppy.",
    "Why did the chicken join a band? Because it had the drumsticks.",
    "I asked the gym instructor if he could teach me to do the splits. He replied, 'How flexible are you?' I said, 'I can't make it on Tuesdays.'",
    "The rotation of the earth really makes my day.",
    "Did you hear about the claustrophobic astronaut? He just needed a little space.",
    "I used to be indecisive. Now I'm not sure.",
    "A clean house is a sign of a broken computer.",
    "I wasn't originally going to get a brain transplant, but then I changed my mind.",
    "Why don't some couples go to the gym? Because some relationships don't work out.",
    "What's orange and sounds like a parrot? A carrot.",
    "Why did the coffee file a police report? It got mugged.",
    "I'm great at multitasking. I can waste time, be unproductive, and procrastinate all at once.",
    "My therapist says I have a preoccupation with vengeance. We'll see about that.",
    "I'm reading a book on anti-gravity. It's impossible to put down.",
    "I'm not addicted to caffeine. We're just in a committed relationship.",
    "I know they say that money talks, but all mine says is 'Goodbye.'",
    "I told my wife she should embrace her mistakes… She gave me a hug.",
    "I'm on a seafood diet. I see food and I eat it.",
    "The man who invented autocorrect should burn in hello.",
    "Life is short. Smile while you still have teeth.",
    "I started out with nothing, and I still have most of it.",
    "If you think nobody cares if you're alive, try missing a couple of car payments.",
    "I dream of a better world where chickens can cross the road without having their motives questioned.",
    "Insomnia is awful. But on the plus side – only three more sleeps until Christmas.",
    "I broke my finger last week. On the other hand, I'm okay.",
    "I'm writing a book on reverse psychology. Don't buy it.",
    "Some people graduate with honors, I am just honored to graduate.",
    "Alcohol doesn't solve any problems, but neither does milk.",
    "Why do bees have sticky hair? Because they use honeycombs.",
    "Age is just a number. In my case, a very big one.",
    "Dark humor is like food. Not everyone gets it.",
    "I'm not short. I'm just more down to Earth than other people.",
    "I used to be a narcissist… but now I'm just perfect.",
    "Sometimes I wonder if I'm a good person, then I remember I give people my Netflix password.",
    "If you think education is expensive, try ignorance.",
    "Whoever stole my copy of Microsoft Office, I will find you. You have my Word.",
    "I know I'm a catch. I just forgot what kind of bait I need.",
    "They say love is blind. Marriage is a real eye-opener.",
    "Sometimes I shock myself with the smart stuff I say. Then I laugh and go get some snacks.",
    "Puns about monorails always make for decent one-liners.",
    "Why did the golfer bring two pairs of pants? In case he got a hole in one.",
    "If we shouldn't eat at night, why is there a light in the fridge?",
    "I'm not weird. I'm limited edition.",
    "I'm not lazy, I'm on standby mode.",
    "I'm writing a book on how to fall down stairs. It's a step-by-step guide.",
    "When life shuts a door… open it again. It's a door. That's how they work.",
    "I tried to be normal once. Worst two minutes of my life.",
    "Sarcasm: because beating people is illegal.",
    "Dear Math, I'm not a therapist. Solve your own problems.",
    "Zombies eat brains. Don't worry, you're safe.",
    "You think you're smarter than me? I graduated in the top 90% of my class!",
    "My password is the last 8 digits of π. Good luck.",
    "I'm not shy. I'm just holding back my awesomeness so I don't intimidate you.",
    "I got a job at a bakery because I kneaded dough.",
    "People say nothing is impossible, but I do nothing every day.",
    "When life gives you melons, you might be dyslexic.",
    "I like to name my dog 'Five Miles' so I can say I walk Five Miles every day.",
    "If Monday had a face, I'd punch it.",
    "I don't have an attitude problem. You have a perception problem.",
    "Don't you hate it when someone answers their own questions? I do.",
    "Not all math puns are bad. Just sum.",
    "My life feels like a test I didn't study for.",
    "I can handle pain. Until it hurts.",
    "My brain has too many tabs open.",
    "If I were a superhero, my power would be napping.",
    "I'm not great at the advice. Can I interest you in a sarcastic comment?",
    "They say don't try this at home… so I went to my friend's house.",
    "I asked Siri why I'm still single. She opened the front camera.",
    "I ate a clock yesterday. It was very time-consuming.",
    "I'm reading a horror story in Braille. Something bad is going to happen, I can feel it.",
    "My favorite machine at the gym is the vending machine.",
    "If at first you don't succeed, then skydiving definitely isn't for you.",
    "Don't worry if plan A doesn't work out. There are 25 more letters.",
    "I don't have gray hair, I have wisdom highlights.",
    "The difference between stupidity and genius is that genius has its limits.",
    "I accidentally handed my wife a glue stick instead of chapstick. She still isn't talking to me.",
    "I asked the librarian if the library had books on paranoia. She whispered, 'They're right behind you…'",
    "Time flies like an arrow. Fruit flies like a banana.",
    "Before you judge someone, walk a mile in their shoes. Then you're a mile away and you have their shoes."
]

# Quotes database
QUOTES = [
    ("The only way to do great work is to love what you do.", "Steve Jobs"),
    ("You may delay, but time will not.", "Benjamin Franklin"),
    ("Procrastination is the art of keeping up with yesterday.", "Don Marquis"),
    ("Life is what happens when you're busy making other plans.", "John Lennon"),
    ("Don't watch the clock; do what it does. Keep going.", "Sam Levenson"),
    ("Success is not final, failure is not fatal: it is the courage to continue that counts.", "Winston Churchill"),
    ("Never put off till tomorrow what may be done day after tomorrow just as well.", "Mark Twain"),
    ("In the middle of every difficulty lies opportunity.", "Albert Einstein"),
    ("Procrastination is opportunity's assassin.", "Victor Kiam"),
    ("Don't wait. The time will never be just right.", "Napoleon Hill"),
    ("If you want to make an easy job seem mighty hard, just keep putting off doing it.", "Olin Miller"),
    ("You miss 100% of the shots you don't take.", "Wayne Gretzky"),
    ("A year from now you may wish you had started today.", "Karen Lamb"),
    ("Amateurs sit and wait for inspiration, the rest of us just get up and go to work.", "Stephen King"),
    ("Do not dwell in the past, do not dream of the future, concentrate the mind on the present moment.", "Buddha"),
    ("Action is the foundational key to all success.", "Pablo Picasso"),
    ("Only put off until tomorrow what you are willing to die having left undone.", "Pablo Picasso"),
    ("Life is really simple, but we insist on making it complicated.", "Confucius"),
    ("The future depends on what you do today.", "Mahatma Gandhi"),
    ("The way to get started is to quit talking and begin doing.", "Walt Disney"),
    ("It always seems impossible until it's done.", "Nelson Mandela"),
    ("Time is a created thing. To say 'I don't have time' is like saying 'I don't want to.'", "Lao Tzu"),
    ("Don't ruin a good today by thinking about a bad yesterday.", "Unknown"),
    ("Someday is not a day of the week.", "Denise Brennan-Nelson"),
    ("He who waits to do a great deal of good at once will never do anything.", "Samuel Johnson"),
    ("Work while it is called today, for you know not how much you may be hindered tomorrow.", "Matthew Henry"),
    ("You cannot escape the responsibility of tomorrow by evading it today.", "Abraham Lincoln"),
    ("Procrastination is the grave in which opportunity is buried.", "Unknown"),
    ("Do something today that your future self will thank you for.", "Sean Patrick Flanery"),
    ("What is not started today is never finished tomorrow.", "Johann Wolfgang von Goethe"),
    ("Life isn't about finding yourself. Life is about creating yourself.", "George Bernard Shaw"),
    ("Things may come to those who wait, but only the things left by those who hustle.", "Abraham Lincoln"),
    ("If you spend too much time thinking about a thing, you'll never get it done.", "Bruce Lee"),
    ("Take time to deliberate; but when the time for action arrives, stop thinking and go in.", "Napoleon Bonaparte"),
    ("Don't be pushed around by the fears in your mind. Be led by the dreams in your heart.", "Roy T. Bennett"),
    ("Time is what we want most, but what we use worst.", "William Penn"),
    ("If you wait, all that happens is you get older.", "Mario Andretti"),
    ("The best way out is always through.", "Robert Frost"),
    ("Time flies over us, but leaves its shadow behind.", "Nathaniel Hawthorne"),
    ("Yesterday is gone. Tomorrow has not yet come. We have only today. Let us begin.", "Mother Teresa"),
    ("Life is short, and it is up to you to make it sweet.", "Sarah Louise Delany"),
    ("The key is not to prioritize what's on your schedule, but to schedule your priorities.", "Stephen Covey"),
    ("You can't build a reputation on what you are going to do.", "Henry Ford"),
    ("Motivation is what gets you started. Habit is what keeps you going.", "Jim Ryun"),
    ("Don't let what you cannot do interfere with what you can do.", "John Wooden"),
    ("Even if you're on the right track, you'll get run over if you just sit there.", "Will Rogers"),
    ("If you're going through hell, keep going.", "Winston Churchill"),
    ("A goal without a plan is just a wish.", "Antoine de Saint-Exupéry"),
    ("Life begins at the end of your comfort zone.", "Neale Donald Walsch"),
    ("Sometimes later becomes never. Do it now.", "Unknown"),
    ("It does not matter how slowly you go as long as you do not stop.", "Confucius"),
    ("Start where you are. Use what you have. Do what you can.", "Arthur Ashe"),
    ("Hard work beats talent when talent doesn't work hard.", "Tim Notke"),
    ("Discipline is choosing between what you want now and what you want most.", "Abraham Lincoln"),
    ("Don't wait for inspiration. It comes while one is working.", "Henri Matisse"),
    ("The expert in anything was once a beginner.", "Helen Hayes"),
    ("Success usually comes to those who are too busy to be looking for it.", "Henry David Thoreau"),
    ("The trouble is, you think you have time.", "Jack Kornfield"),
    ("Life is 10% what happens to you and 90% how you react to it.", "Charles R. Swindoll"),
    ("Make each day your masterpiece.", "John Wooden"),
    ("You must be the change you wish to see in the world.", "Mahatma Gandhi"),
    ("The man who moves a mountain begins by carrying away small stones.", "Confucius"),
    ("A journey of a thousand miles begins with a single step.", "Lao Tzu"),
    ("You get in life what you have the courage to ask for.", "Oprah Winfrey"),
    ("Dream big and dare to fail.", "Norman Vaughan"),
    ("Opportunities are usually disguised as hard work, so most people don't recognize them.", "Ann Landers"),
    ("Don't count the days, make the days count.", "Muhammad Ali"),
    ("I never dreamed about success. I worked for it.", "Estée Lauder"),
    ("Either you run the day, or the day runs you.", "Jim Rohn"),
    ("There are no shortcuts to any place worth going.", "Beverly Sills"),
    ("Don't be afraid to give up the good to go for the great.", "John D. Rockefeller"),
    ("If you don't design your own life plan, chances are you'll fall into someone else's plan.", "Jim Rohn"),
    ("If not now, when?", "Hillel the Elder"),
    ("Success is getting what you want. Happiness is wanting what you get.", "Dale Carnegie"),
    ("The secret of getting ahead is getting started.", "Mark Twain"),
    ("You don't have to be great to start, but you have to start to be great.", "Zig Ziglar"),
    ("Great acts are made up of small deeds.", "Lao Tzu"),
    ("Your time is limited, so don't waste it living someone else's life.", "Steve Jobs"),
    ("Lost time is never found again.", "Benjamin Franklin"),
    ("A wise person does at once what a fool does at last.", "Baltasar Gracián"),
    ("Don't wait until everything is just right. It will never be perfect.", "Mark Victor Hansen"),
    ("Better three hours too soon than a minute too late.", "William Shakespeare"),
    ("If you want to achieve greatness stop asking for permission.", "Anonymous"),
    ("Push yourself, because no one else is going to do it for you.", "Anonymous"),
    ("The best time to plant a tree was 20 years ago. The second best time is now.", "Chinese Proverb"),
    ("Don't limit your challenges. Challenge your limits.", "Jerry Dunn"),
    ("You can't cross the sea merely by standing and staring at the water.", "Rabindranath Tagore"),
    ("What lies behind us and what lies before us are tiny matters compared to what lies within us.", "Ralph Waldo Emerson"),
    ("Believe you can and you're halfway there.", "Theodore Roosevelt"),
    ("You don't need more time, you just need to decide.", "Seth Godin"),
    ("Doing nothing is very hard to do… you never know when you're finished.", "Leslie Nielsen"),
    ("Delaying tactics are the art of self-sabotage.", "Unknown"),
    ("You have to expect things of yourself before you can do them.", "Michael Jordan"),
    ("Don't wait for the perfect moment. Take the moment and make it perfect.", "Unknown"),
    ("Just do it.", "Nike"),
    ("Stop waiting. Start creating.", "Unknown"),
    ("You can't start the next chapter if you keep re-reading the last one.", "Unknown"),
    ("Do it now. Sometimes 'later' becomes 'never'.", "Unknown")
]

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN or TOKEN == 'your_bot_token_here':
    logger.error('No valid bot token found in .env file')
    exit(1)

async def track_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Track user activity for active member stats."""
    if not update.message or not update.effective_user:
        return
    
    user_id = update.effective_user.id
    now = datetime.now()
    
    # Update user activity
    active_members[user_id]['messages'] += 1
    active_members[user_id]['last_active'] = now
    active_members[user_id]['username'] = update.effective_user.username or f"user_{user_id}"
    active_members[user_id]['full_name'] = update.effective_user.full_name
    
    # Update weekly and monthly stats
    weekly_stats[user_id] += 1
    monthly_stats[user_id] += 1
    
    # Reset weekly stats every Monday
    if (now - last_weekly_reset).days >= 7 and now.weekday() == 0:  # Monday
        weekly_stats.clear()
        last_weekly_reset = now
    
    # Reset monthly stats on the first day of the month
    if now.month != last_monthly_reset.month:
        monthly_stats.clear()
        last_monthly_reset = now

async def send_random_sticker(chat_id, context):
    """Send a random sticker to the chat."""
    max_retries = 5  # Increased number of retries
    last_error = None
    
    # First, try fallback stickers
    for _ in range(max_retries):
        try:
            sticker_id = random.choice(FALLBACK_STICKERS)
            await context.bot.send_sticker(chat_id=chat_id, sticker=sticker_id)
            return True
        except Exception as e:
            last_error = e
            logger.warning(f"Fallback sticker attempt failed: {e}")
            await asyncio.sleep(0.5)  # Small delay between retries
    
    # If fallback stickers fail, try sticker sets
    if STICKER_SETS:
        for _ in range(max_retries):
            try:
                sticker_set_name = random.choice(STICKER_SETS)
                sticker_set = await context.bot.get_sticker_set(sticker_set_name)
                if sticker_set.stickers:
                    sticker = random.choice(sticker_set.stickers)
                    await context.bot.send_sticker(chat_id=chat_id, sticker=sticker.file_id)
                    return True
            except Exception as e:
                last_error = e
                logger.warning(f"Sticker set attempt failed: {e}")
                await asyncio.sleep(0.5)
    
    # If we get here, all attempts failed
    error_msg = f"All attempts to send sticker failed. Last error: {last_error}"
    logger.error(error_msg)
    raise Exception(error_msg)

async def sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a random sticker."""
    try:
        # Send a typing action to show the bot is working
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action='choose_sticker'
        )
        
        # Send the sticker with retries
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                await send_random_sticker(update.effective_chat.id, context)
                return  # Success, exit the function
                
            except Exception as e:
                logger.warning(f"Sticker attempt {attempt + 1} failed: {e}")
                if attempt == max_attempts - 1:  # Last attempt
                    raise
                await asyncio.sleep(1)  # Wait before retry
                
    except Exception as e:
        logger.error(f"All sticker attempts failed: {e}")
        try:
            # As a last resort, try to send a text message
            await update.message.reply_text(
                "🎭 Sticker service is temporarily unavailable. "
                "I'll be back with more stickers soon! 🎨"
            )
        except Exception as text_error:
            logger.error(f"Failed to send error message: {text_error}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    logger.info(f"Start command received from {update.effective_user.id}")
    try:
        # Send welcome message
        await update.message.reply_text(
            '👋 Welcome to the group! I am your welcome bot.\n\n'
            'Available commands:\n'
            '/joke - Get a random joke\n'
            '/quote - Get an inspirational quote\n'
            '/sticker - Get a random sticker\n'
            '/topweekly - Show most active members this week\n'
            '/topmonthly - Show most active members this month'
        )
        
        # Send a welcome sticker
        await send_random_sticker(update.effective_chat.id, context)
    except Exception as e:
        logger.error(f"Error in start command: {e}")

async def joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a random joke."""
    try:
        joke = random.choice(JOKES)
        await update.message.reply_text(f"🎭 {joke}")
    except Exception as e:
        logger.error(f"Error in joke command: {e}")
        await update.message.reply_text("I'm all out of jokes for now!")

async def quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a random inspirational quote."""
    try:
        quote, author = random.choice(QUOTES)
        await update.message.reply_text(f'"{quote}"\n— {author}')
    except Exception as e:
        logger.error(f"Error in quote command: {e}")
        await update.message.reply_text("I'm fresh out of wisdom for now!")

async def top_weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show most active members this week."""
    try:
        if not weekly_stats:
            await update.message.reply_text("No activity stats for this week yet!")
            return
            
        sorted_users = sorted(weekly_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        message = "🏆 *Top Active Members This Week* 🏆\n\n"
        
        for idx, (user_id, count) in enumerate(sorted_users, 1):
            user = active_members.get(user_id, {})
            username = user.get('username', f"user_{user_id}")
            full_name = user.get('full_name', 'Unknown User')
            message += f"{idx}. {full_name} (@{username}): {count} messages\n"
            
        await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in top_weekly command: {e}")
        await update.message.reply_text("Couldn't fetch weekly stats right now.")

async def top_monthly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show most active members this month."""
    try:
        if not monthly_stats:
            await update.message.reply_text("No activity stats for this month yet!")
            return
            
        sorted_users = sorted(monthly_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        message = "🏆 *Top Active Members This Month* 🏆\n\n"
        
        for idx, (user_id, count) in enumerate(sorted_users, 1):
            user = active_members.get(user_id, {})
            username = user.get('username', f"user_{user_id}")
            full_name = user.get('full_name', 'Unknown User')
            message += f"{idx}. {full_name} (@{username}): {count} messages\n"
            
        await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in top_monthly command: {e}")
        await update.message.reply_text("Couldn't fetch monthly stats right now.")

async def left_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when a member leaves the group."""
    left_member = update.message.left_chat_member
    if left_member and left_member.id != context.bot.id:  # Don't send message if bot is the one who left
        try:
            await update.message.reply_text(
                f"👋 {left_member.mention_html()}, we're sorry to see you go! You'll be missed!",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Error sending left chat message: {e}")

async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when a new member joins the group."""
    logger.info("=== NEW MEMBER DETECTED ===")
    logger.info(f"Update content: {update}")
    
    # Check if this is a message with new chat members
    if update.message and update.message.new_chat_members:
        logger.info(f"Processing new chat members in message {update.message.message_id}")
        logger.info(f"Chat ID: {update.effective_chat.id}")
        logger.info(f"Chat type: {update.effective_chat.type}")
        logger.info(f"New members: {update.message.new_chat_members}")
        
        for member in update.message.new_chat_members:
            # Skip if the new member is the bot itself
            if member.is_bot and member.id == context.bot.id:
                logger.info("Bot was added to the group")
                continue
                
            try:
                # Get member count
                chat_member_count = await context.bot.get_chat_member_count(update.effective_chat.id)
                
                # Create welcome message with proper MarkdownV2 escaping
                welcome_msg = (
                    f"👋 Welcome {member.mention_markdown_v2()} to the group\!\n"
                    f"You are member {'#' + str(chat_member_count)} 🎉"
                )
                
                # Send welcome message
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=welcome_msg,
                    parse_mode='MarkdownV2',
                    reply_to_message_id=update.message.message_id
                )
                
                # Send a welcome sticker
                await send_random_sticker(update.effective_chat.id, context)
                logger.info(f"Welcome message sent to {member.full_name}")
                
            except Exception as e:
                logger.error(f"Error welcoming {member.full_name}: {e}")
    else:
        logger.warning("No new members found in the update")
    
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
                f"👋 Welcome aboard MATE, {member.mention_markdown_v2()}! 🎉\n"
                f"You're member #{chat_member_count}!",
                
                f"👋 Welcome aboard MATE, {member.mention_markdown_v2()}! 🎉\n"
                f"Great to have you as member #{chat_member_count}!",
                
                f"👋 Welcome aboard MATE, {member.mention_markdown_v2()}! 🎉\n"
                f"Thrilled to have you join us! You're member #{chat_member_count}"
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
                # Fallback simple welcome with HTML parsing instead of Markdown
                await update.message.reply_text(
                    f"👋 Welcome aboard MATE, {member.mention_html()}! 🎉",
                    parse_mode='HTML'
                )
            except Exception as fallback_error:
                logger.error(f"Fallback welcome failed: {fallback_error}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by Updates."""
    logger.error(f"Error while processing update: {update}", exc_info=context.error)

async def check_bot_info(bot):
    """Check bot info and permissions."""
    try:
        me = await bot.get_me()
        logger.info(f"Bot info: @{me.username} (ID: {me.id})")
        return True
    except Exception as e:
        logger.error(f"Failed to get bot info: {e}")
        return False

async def main_async():
    """Async entry point for the bot."""
    try:
        # Create the Application with proper event loop
        application = (
            Application.builder()
            .token(TOKEN)
            .build()
        )
        logger.info("Application created successfully")
        
        # Check bot info and permissions
        if not await check_bot_info(application.bot):
            logger.error("Failed to initialize bot. Check your token and internet connection.")
            return
        
        # Add command handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("joke", joke))
        application.add_handler(CommandHandler("quote", quote))
        application.add_handler(CommandHandler("sticker", sticker))
        application.add_handler(CommandHandler("topweekly", top_weekly))
        application.add_handler(CommandHandler("topmonthly", top_monthly))
        
        # Handle new members and left members
        application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))
        application.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, left_chat_member))
        
        # Track all messages for activity
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            track_activity
        ))
        
        # Error handler
        application.add_error_handler(error_handler)
        
        logger.info("All handlers registered")
        
        # Log bot info
        me = await application.bot.get_me()
        logger.info(f"Starting bot: @{me.username} (ID: {me.id})")
        logger.info("Bot is running. Press Ctrl+C to stop")
        
        # Start the Bot
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        # Keep the bot running
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"Error in main_async: {e}")
        raise

def main():
    """Start the bot."""
    try:
        # Create a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the bot
        loop.run_until_complete(main_async())
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot stopped with error: {e}")
    finally:
        # Cleanup
        if 'loop' in locals():
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()

if __name__ == '__main__':
    main()
