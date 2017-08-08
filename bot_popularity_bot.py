import praw
from time import sleep
import schedule
import bot_data as d

app_secret = d.app_secret
app_ID = d.app_ID
app_URI = d.app_URI
app_user_agent = d.app_user_agent
app_refresh_token = d.app_refresh_token

del(d)

response = "Thanks for your {feedback_type} feedback! {total_votes} {people} voted on {bot_name} so far, with {upvotes} positive votes and {downvotes} negative votes, giving {bot_name} a popularity of {popularity}%.\n\nSee the [current leaderboard here](/r/botpopularitybot/wiki/bot_popularity). Source [here](https://github.com/Theonefoster/bot_popularity_bot/blob/master/bot_popularity_bot.py)."

def login():
    print("logging in..")
    r = praw.Reddit(app_user_agent, disable_update_check=True)
    r.set_oauth_app_info(app_ID ,app_secret, app_URI)
    r.refresh_access_information(app_refresh_token)
    print("logged in as " + str(r.user.name))
    return r

def sort_bots():
    global all_bots
    bots = list(all_bots)
    scores = []
    output = []
  #sort by popularity percentage:
  #  for bot in bots:
  #      total_votes = bot_scores[bot][0]
  #      current_score = bot_scores[bot][1]
  #      upvotes = int(total_votes - ((total_votes - current_score)/2))
  #      popularity = (upvotes/total_votes) * 100 #in percent
  #      scores.append(popularity)

    #sort by current score (upvotes-downvotes)
    for bot in bots:
      scores.append(bot_scores[bot][1]) #get current score

    while scores != []: #simple selection sort
        lowest = 100
        index = -1 #default to last item

        for bot in scores:
            if bot < lowest:
                lowest = bot
                index = scores.index(bot)

        output.append(bots[index])
        del bots[index]
        del scores[index]

    bots
    return output

def update_wikis():
    #update database
    r.edit_wiki_page("botpopularitybot", "scores", str(bot_scores))
    print("Scores wiki updated!")

    #update public leaderboard (not sorted: TODO)
    header = "Bot Name|Approvals|Disapprovals|Current Score|Popularity\n:--|:--|:--|:--|:--\n"
    row = "[{bot_name}]({bot_profile})|{upvotes}|{downvotes}|{current_score}|{popularity}%\n"

    output = header

    for bot in sort_bots()[::-1]:
        bot_name = bot
        current_score = bot_scores[bot][1]
        total_votes = bot_scores[bot][0]
        upvotes = int(total_votes - ((total_votes - current_score)/2))
        downvotes = total_votes - upvotes
        popularity = round((upvotes/total_votes) * 100, 1) #in percent
        output += row.format(bot_name=bot_name, 
                                bot_profile = "https://www.reddit.com/u/" + bot_name, 
                                upvotes=upvotes, downvotes=downvotes, 
                                current_score=current_score, 
                                popularity=popularity)

    r.edit_wiki_page("botpopularitybot", "bot_popularity", output)
    print("Leaderboard wiki updated!")

r = login() # works
subreddit = r.get_subreddit("botpopularitybot")
wiki_page = subreddit.get_wiki_page("scores").content_md
bot_scores = eval(wiki_page) #dict of form {"bot name": [total_votes, current score]}
all_bots = list(bot_scores.keys())
feed = praw.helpers.comment_stream(r, "all")

schedule.every(2).minutes.do(update_wikis)

for comment in feed:
    schedule.run_pending()
    try:
        body = comment.body.lower()
        if body[:8] == "good bot" or body[:7] == "bad bot":
            parent_id = comment.parent_id
            parent = r.get_info(thing_id=parent_id)
            bot_name = parent.author.name

            if bot_name not in bot_scores:
                bot_scores[bot_name] = [0,0]

            bot_scores[bot_name][0] += 1

            if body[:8] == "good bot":
                bot_scores[bot_name][1] += 1
                feedback_type = "positive"
            else:
                bot_scores[bot_name][1] -= 1
                feedback_type = "negative"

            current_score = bot_scores[bot_name][1]
            total_votes=bot_scores[bot_name][0]
            upvotes = int(total_votes - ((total_votes - current_score)/2))
            downvotes = total_votes - upvotes
            popularity = round((upvotes/total_votes) * 100, 1) #in percent

            if total_votes > 1: 
                people = "people have" 
            else:
                people = "person has"

            reply_to_send = response.format(feedback_type=feedback_type, people=people, total_votes=total_votes, bot_name=bot_name, upvotes=upvotes, downvotes=downvotes, popularity=popularity)
            comment.reply(reply_to_send)
            print("Replied to " + comment.author.name + " regarding bot " + bot_name)

    except Exception as e:
        print("Unknown error: " + str(e))
