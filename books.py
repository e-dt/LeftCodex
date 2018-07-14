#!/usr/bin/env python3.6
#This file is in the public domain.
import discord
from discord.ext import commands
import asyncio
import math
import pickle

bot = commands.Bot(command_prefix='b)')
books_table = {}
booklist = [i.strip().split(',,') for i in open("booklist.txt", encoding="utf-8").readlines()]
#TITLE AUTHOR FILENAME COVERURL
#TITLE AUTHOR FILENAME COVERURL
#etc

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    

class Book:
    def __init__(self, bookfile, cover, title: str, author: str, message, current: int = -30):
        self.bookfile   = bookfile
        self.cover      = cover
        self.title      = title
        self.author     = author
        self.message    = message
        self.booklines  = open(bookfile, 'r', encoding="utf-8").readlines()
        self.current    = current
        self.pagecount  = math.floor(len(booklines)/30)
        
        
    async def update(self):
        text = "".join(self.booklines[self.current : self.current + 30])
        em =  discord.Embed(
                    title = self.title + " by " + self.author,
                    description = text
        )
        em.set_footer(text="Page " + str(math.floor(self.current/30)+1), + " of " + str(self.pagecount))
        await self.message.edit(embed = em)
    def next_page(self):
        self.current += 30

    def prev_page(self):
        self.current -= 30

    def skip_ten(self):
        self.current += 300
    
    def back_ten(self):
        self.current -= 300


    async def dispatch_reaction(self, emoji):
        if   emoji == "⬅":
            self.prev_page()
            await self.update()
        elif emoji == "➡":
            self.next_page()
            await self.update()
        elif emoji == "⏪":
            self.back_ten()
            await self.update()
        elif emoji == "⏩":
            self.skip_ten()
            await self.update()

def book_to_dict(book):
    return {"bookfile": book.bookfile,
            "cover": book.cover,
            "title": book.title,
            "author": book.author,
            "message_id": book.message.id,
            "channel_id": book.message.channel.id,
            "current": book.current}

async def dict_to_book(d):
    message_channel =  bot.get_channel(d['channel_id'])
    message = await message_channel.get_message(d['message_id'])
    return Book(d['bookfile'], d['cover'], d['title'], d['author'], message, d['current'])

@bot.command(name = 'codex')
async def codex(ctx, tendency: str = None):
    """Shows a list of all books in tendency specified. If tendency not specified, shows a list of tendencies."""
    if tendency == None:
        await ctx.send("Tendencies: ```\n"+ "\n".join({i[4] for i in booklist}) + "```\nChoose a tendency to view using `b)codex <tendency>`.")
        return
    tendencylist = [i for i in booklist if i[4] == tendency.lower()]
    await ctx.send("Choose books from this list, using `b)read <id>`.\n```\n"
                   + "\n".join([book[0] + " by " + book[1] + ". ID: "
                                + book[2] for book in tendencylist])
                   + "```")

@bot.command(name = 'read')
async def read(ctx, id, channel: discord.TextChannel = None):
    """Read book specified by id given in channel specified. If channel not specified, it is the channel the command is sent in."""
    channelid = channel.id if channel != None else ctx.channel.id
    channel = ctx.channel if channel == None else channel
    row = list(filter(lambda x: x[2] == id.lower(), booklist))[0]
    em = discord.Embed(title = row[0] + " by " + row[1])
    em.set_image(url = row[3])
    message = await channel.send(embed = em)
    await message.add_reaction("⏪")
    await message.add_reaction("⬅")
    await message.add_reaction("➡")
    await message.add_reaction("⏩")
    books_table[channelid] = Book(id, row[3], row[0], row[1], message)

@bot.event
async def on_raw_reaction_add(emoji, message_id, channel_id, user_id):
    if user_id == 466890219803639810: #hacky but w/e
        return
    book = books_table[channel_id]
    if book.message.id != message_id:
        return
    c = bot.get_channel(channel_id)
    m = await c.get_message(message_id)
    await m.remove_reaction(emoji, bot.get_user(user_id))
    await book.dispatch_reaction(emoji.name)

@bot.command(name = 'reload')
@commands.is_owner()
async def reload(ctx):
    global booklist
    booklist = [i.strip().split(',,') for i in open("booklist.txt", encoding="utf-8").readlines()]
    print([i[0]+str(len(i)) for i in booklist])

@bot.command(name = "jump")
async def jump(ctx, page: int, channel: discord.TextChannel = None):
    """Jumps to a page in the book in the channel specified. If channel not specified, it is the channel the command is sent in."""
    channelid = channel.id if channel != None else ctx.channel.id
    line = 30 * (page-1)
    book = books_table[channelid]
    book.current = line
    await book.update()

@bot.command(name = "hither")
async def hither(ctx, channel: discord.TextChannel = None):
    """Moves the book in the channel specified to the bottom. If channel not specified, it is the channel the command is sent in."""
    channelid = channel.id if channel != None else ctx.channel.id
    channel = ctx.channel if channel == None else channel
    book = books_table[channelid]
    em = discord.Embed(title = book.title + " by " + book.author)
    em.set_image(url = book.cover)
    message = await channel.send(embed = em)
    await message.add_reaction("⏪")
    await message.add_reaction("⬅")
    await message.add_reaction("➡")
    await message.add_reaction("⏩")
    books_table[channelid] = Book(book.bookfile, book.cover, book.title, book.author, message)
    books_table[channelid].current = book.current
    await books_table[channelid].update()
@bot.command(name = "suggest")
async def suggest(ctx, *, book: str):
    """Suggests a book."""
    suggestion_channel = bot.get_channel(467642671519760394)
    await suggestion_channel.send("Suggestion: " + book)
    await ctx.send("Sent the suggestion to the suggestion channel in this bot's server. https://discord.gg/azkEP4S to learn more.")

@bot.command(name = "server")
async def server(ctx):
    """Sends a link to the support server."""
    await ctx.send("This bot's server can be found at https://discord.gg/azkEP4S.")
@bot.command(name = "save")
@commands.is_owner()
async def save(ctx):
    table = {channel : book_to_dict(book) for channel, book in books_table.items()}
    pickle.dump(table, open("saved.pickle", "wb"), -1)
    await ctx.send("saved.")

@bot.command(name = "load")
@commands.is_owner()
async def load(ctx):
    global books_table
    books_table = {channel : await dict_to_book(d) for channel, d in pickle.load(open("saved.pickle", "rb")).items()}
    await ctx.send("restored.")
bot.run(open(".token","r").read(), reconnect=True)
