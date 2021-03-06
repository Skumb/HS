from django.http import HttpResponse
import json
import os
from hearthstone.models import Hero, Minion, Card, Spell, Deck, Party, UserCard, Chat, Forum, Topic, Post, Follow, Room
from random import randint
from pprint import pprint
from django.shortcuts import render, redirect, get_object_or_404, render_to_response
from django.template import loader
from .forms import UserRegisterForm
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
from django.db.models import Q
from django.conf import settings
from hearthstone.settings import *
from django.template import RequestContext
from django.forms import models as forms_models
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core.paginator import Paginator
from hearthstone.forms import TopicForm, PostForm




def index(request):
    if not Hero.objects.all():
        module_dir = os.path.dirname(__file__)  # get current directory
        file_path = os.path.join(module_dir, 'cards.json')
        with open(file_path) as f:
            data = json.load(f)

        for card in data["Basic"]:
                #enchantements not used
                if card["type"] == "Spell":

                    Spell.objects.create(
                        name=card.get("name"),
                        playerClass=card.get("playerClass"),
                        cost=card.get("cost", 0),
                        img_url=card.get("img", "https://i.imgur.com/U1dkXzQ.png"),
                        rarity=card.get("rarity","NAN"),
                    )

                elif card["type"] == "Hero":

                    Hero.objects.create(
                        name=card.get("name"),
                        playerClass=card.get("playerClass")
                    )

        decks = ["Basic","Classic","Naxxramas","Goblins vs Gnomes","The Grand Tournament"]
        for deck in decks:
                    
            for card in data[deck]:
                if card["type"] != "Minion":
                    continue

                Minion.objects.create(
                    name=card.get("name"),
                    cost=card.get("cost",0),
                    attack=card.get("attack",0),
                    health=card.get("health",1),
                    playerClass=card.get("playerClass"),
                    rarity= card.get("rarity","NAN"),
                    img_url=card.get("img","https://i.imgur.com/U1dkXzQ.png"),
                )

    if Party.objects.all() != False and request.user.id != False:
        games = Party.objects.all().filter(Q(attaquant=request.user.id) | Q(defenseur=request.user.id))
    else:
        games = ""
                
    return render(request, 'hearthstone/index.html', {'games': games})

def home(request):
    title = 'Accueil'
    context = {
        'title': title,
        'parties': Party.objects.all(),
        'Hero': Hero.objects.all(),
        'userList': User.objects.values()
    }
    return render(request, 'hearthstone/index.html', context)

@csrf_exempt
def send_mmes(request):
    if request.is_ajax():
        myId = User.objects.get(id=request.POST['myId'])
        hisId = User.objects.get(id=request.POST['hisId'])
        message = request.POST['txt']

        send = Chat(msg=message, userFrom = myId , userTo = hisId)
        send.save()
 
    return HttpResponse(message)

@csrf_exempt
def get_mmes(request):
    myId = User.objects.get(id=request.POST['myId'])
    hisId = User.objects.get(id=request.POST['hisId'])
    messageList = Chat.objects.filter(Q(userTo=myId) | Q(userFrom=myId)).filter(Q(userTo=hisId) | Q(userFrom=hisId))
    messageList_json = serializers.serialize('json', messageList)
    return HttpResponse(messageList_json, content_type='application/json')

@csrf_exempt
def change_troc(request):
    card = UserCard.objects.get(id=request.POST['idCard'])
    card.troc = request.POST['value']
    card.save()
    message = request.POST['value']

    return HttpResponse(message, content_type='application/json')

@csrf_exempt
def change_follow(request):

    if not Follow.objects.all().filter(userFrom = request.POST['mnid']).filter(userTo = request.POST['idUser']):

        user1 = User.objects.get(id=request.POST['mnid'])
        user2 = User.objects.get(id=request.POST['idUser'])

        follow = Follow(userFrom = user1, userTo = user2 , value = request.POST['value'])
        follow.save()

    else:

        user1 = User.objects.get(id=request.POST['mnid'])
        user2 = User.objects.get(id=request.POST['idUser'])

        follow = Follow.objects.get(userFrom = user1, userTo = user2)
        follow.value = request.POST['value']
        follow.save()

    message = request.POST['value']

    return HttpResponse(message, content_type='application/json')


@csrf_exempt
def get_follow(request):

    try:
        user1 = User.objects.get(id=request.POST['myId'])
        user2 = User.objects.get(id=request.POST['hisId'])
        follow = Follow.objects.get(userFrom = user1, userTo = user2)
        messageList_json = serializers.serialize('json', [ follow, ])
        return HttpResponse(messageList_json, content_type='application/json')
    except Follow.DoesNotExist:
        message = 'ko'
        return HttpResponse(message)

    
    
def getTrocCards(request, user_id):
    cardsTroc = UserCard.objects.filter(user_id=user_id).filter(troc=1).select_related("card")
    user = User.objects.get(id=user_id)

    return render(request, 'hearthstone/troc.html', {'cards': cardsTroc, 'user': user})

def trocChooseCard(request, usercard_id):
    cardsTroc = UserCard.objects.filter(user_id=request.user.id).filter(troc=1).select_related("card")
    return render(request, 'hearthstone/troc_choose.html', {'cards': cardsTroc, 'usercard_id': usercard_id})

def trocValidate(request, usercard_id, myusercard_id):

    card1 = UserCard.objects.get(id=usercard_id)
    lastid = card1.user_id
    card1.user_id = request.user.id
    card1.troc = 0
    card1.save()


    card2 = UserCard.objects.get(id=myusercard_id)
    card2.user_id = lastid
    card2.troc = 0
    card2.save()

    return redirect('check')


def deck_choose(request, str):
    userList = User.objects.values()
    decksUser = Deck.objects.all().filter(user_id=request.user.id).filter(finished=1)
    return render(request, 'hearthstone/choose_deck.html', {'userList': userList, "param": str, "decks": decksUser})

def choosebot(request):
    val = randint(0, 1)

    if val == 0:

        user1 = User.objects.get(id=request.user.id)

        game = Party(attaquant = user1)
        game.save()

    else:

        user1 = User.objects.get(id=request.user.id)

        game = Party(attaquant = user1, gagnant = user1)
        game.save()

        request.user.profile.credit += 100
        request.user.save()

    return redirect('home')

def chooseother(request):
    userList = User.objects.values()
    decksUser = Deck.objects.all().filter(user_id=request.user.id).filter(finished=1)

    if not Room.objects.all().filter(J1__isnull=False, J2__isnull=True):
        user1 = User.objects.get(id=request.user.id)
        room = Room(J1 = user1)
        room.save()
        user2 = ""
        decksOther = ""

    else:
        room = Room.objects.get(J1__isnull=False, J2__isnull=True)
        user2 = User.objects.get(id=request.user.id)
        decksOther = Deck.objects.all().filter(user_id=room.J1).filter(finished=1)
        room.J2 = user2
        room.save()
        user1 = User.objects.get(id=room.J1.id)

        other = decksUser = Deck.objects.all().filter(user_id=request.user.id).filter(finished=1)

    return render(request, 'hearthstone/choose_deck_users.html', {'userList': userList, "param": str, "decks": decksUser, "room": room, "decksOther": decksOther, "user1":user1, "user2":user2})



def chooseotherwin(request, user1_id, user2_id):
    val = randint(0, 1)

    if val == 0:

        user11 = User.objects.get(id=user1_id)
        user22 = User.objects.get(id=user2_id)

        game = Party(attaquant = user11, defenseur = user22, gagnant = user11)
        game.save()

        user11.profile.credit += 100
        user11.save()

    else:

        user11 = User.objects.get(id=user1_id)
        user22 = User.objects.get(id=user2_id)

        game = Party(attaquant = user11, defenseur = user22, gagnant = user22)
        game.save()

        user22.profile.credit += 100
        user22.save()

    return redirect('home')



def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Hello {username}, votre compte a bien été créé !')
            new_user = authenticate(
                username = username,
                password=form.cleaned_data['password1'],
            )
            login(request, new_user)
            for c in Card.objects.filter(rarity="Free"):
                    UserCard.objects.create(user = new_user, card = c, playerClass = c.playerClass, cost = c.cost )
        
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})

def party(request):
    return render(request, 'hearthstone/party.html')

def buyCards(request):
    userList = User.objects.values()
    cardsCounter = Card.objects.all().count()
    cards = []
    if request.user.is_authenticated and request.user.profile.credit >= 100:
        for i in range(8):
            random_index = randint(0, cardsCounter - 1)
            card = Card.objects.all()[random_index]
            cards.append(card)
            userCard = UserCard(user=request.user, card = card , playerClass = card.playerClass , cost = card.cost)
            userCard.save()
        request.user.profile.credit -= 100
        request.user.save()
    elif request.user.is_authenticated and request.user.profile.credit < 100:
        messages.warning(request, f'Vous n\'avez pas assez de crédit :(')
        return redirect('home')
    else:
        messages.warning(request, f'Vous devez être connecté pour accéder à cette page')
        return redirect('home')

    return render(request, 'hearthstone/buy-cards.html', {'cards': cards, 'userList': userList})


def myCards(request):
    userList = User.objects.values()
    cards = UserCard.objects.filter(user_id=request.user.id)
    #Card.objects.all()
    #UserCard.objects.filter(user_id=request.user.id)
    #UserCard.objects.filter(user_id=request.user.id)
    arr = [0,1,2,3,4,5,6,7,8,"9+"]
    return render(request, 'hearthstone/my-cards.html', {'cards': cards.order_by('cost'), 'mana': arr, 'userList': userList})


def sellCard(request, card_id, rarity):

    cards = UserCard.objects.filter(card_id = card_id).filter(user_id = request.user.id)
    cards.delete()
    if rarity == "Free":
        request.user.profile.credit += 0
    elif rarity == "Common":
        request.user.profile.credit += 5
    elif rarity == "Rare":
        request.user.profile.credit += 20
    elif rarity == "Epic":
        request.user.profile.credit += 100
    elif rarity == "Legendary":
        request.user.profile.credit += 400
    request.user.save()
    return redirect('myCards')

def check(request):
    userList = User.objects.values()
    followList = Follow.objects.filter(userFrom = request.user.id).select_related("userFrom")
    return render(request, 'hearthstone/check.html', {'userList': userList, 'followList': followList})

def checkPlayerCards(request, user_id):
    userList = User.objects.values()
    theUser = get_object_or_404(User, pk=user_id)

    cards = UserCard.objects.filter(user_id=user_id)

    arr = [0,1,2,3,4,5,6,7,8,"9+"]

    return render(request, 'hearthstone/check_player_cards.html', {'cards': cards, 'theUser': theUser, 'userList': userList, "mana": arr})

def checkPlayerDeckCards(request, user_id, deck_id):
    userList = User.objects.values()
    theUser = get_object_or_404(User, pk=user_id)
    cards = Card.objects.filter(deck = deck_id)
    deck = get_object_or_404(Deck, pk=deck_id)
    arr = [0,1,2,3,4,5,6,7,8,"9+"]

    return render(request, 'hearthstone/check_player_deck_cards.html', {'userList': userList, 'theUser': theUser, 'cards': cards, "mana": arr, 'deck': deck})

def checkPlayerDecks(request, user_id):
    userList = User.objects.values()
    theUser = get_object_or_404(User, pk=user_id)
    decksUser = Deck.objects.all().filter(user_id=user_id)
    return render(request, 'hearthstone/check_player_decks.html', {'userList': userList, 'theUser': theUser, 'decks': decksUser})

def myDecks(request):
    decksUser = Deck.objects.all().filter(user_id=request.user.id)
    userList = User.objects.values()

    return render(request, 'hearthstone/my-decks.html', {'decks': decksUser, 'userList': userList})


def deck(request, deck_id):
    deck = get_object_or_404(Deck, pk=deck_id)
    userList = User.objects.values()
    
    #idCards = deck.cards

    cards = Card.objects.filter(deck = deck_id)

    return render(request, 'hearthstone/deck.html', {'cards': cards, 'deck': deck, 'userList': userList})

def createDeck(request):

    heros = Hero.objects.all()
    userList = User.objects.values()

    return render(request, 'hearthstone/create-deck.html', {'heros': heros, 'userList': userList})

def createDeckByHero(request, hero_id):

    userList = User.objects.values()
    hero = Hero.objects.get(pk=hero_id)
    #cards = Card.objects.all().filter(playerClass="Druid")  #hero.playerClass
    #cartes = Card.objects.all().filter(playerClass="Druid")  #hero.playerClass
    cardsNeutral = UserCard.objects.filter(user_id=request.user.id).filter(playerClass= "Neutral")
    cardsUser = UserCard.objects.filter(user_id=request.user.id).filter(playerClass=hero.playerClass)
    allCards = cardsUser | cardsNeutral


    arr = [0,1,2,3,4,5,6,7,8,"9+"]

    finished = False;

    if request.POST:
        title = request.POST.get("title", "")
        cards = request.POST.getlist("cards[]", "")

        #cards = list(map(int, cards))


        if len(cards) == 30:
                 finished = True;

        newDeck = Deck.objects.create(
            user=request.user,
            title=title,
            #cards=json.dumps(cards),
            finished=finished
        )

        for card in cards:
            newDeck.cards.add(card)

        decksUser = Deck.objects.all().filter(user_id=request.user.id)

        return render(request, 'hearthstone/my-decks.html', {'decks': decksUser})

    return render(request, 'hearthstone/create-deck-by-hero.html' , {'cards': allCards.order_by('cost'), "mana": arr, 'userList': userList})


def deleteDeck(request, deck_id):
    deck = get_object_or_404(Deck, pk=deck_id)

    deck.delete()

    return redirect('myDecks')


def updateDeck(request, deck_id):
    if request.POST:
        deck = get_object_or_404(Deck, pk=deck_id)

        cards = request.POST.getlist("cards[]", "")
    
        obj = Deck.objects.get(pk= deck_id)
        obj.cards.set(cards)
        obj.save()

        return redirect('deck', deck.pk)
    else:
        deck = get_object_or_404(Deck, pk=deck_id)
    
        idCards = deck.cards
        userList = User.objects.values()

        cardsUser = UserCard.objects.filter(user_id=request.user.id)
        cardsDeck = Card.objects.filter(deck = deck_id)

        l = [cD.id for cD in cardsDeck]

        arr = [0,1,2,3,4,5,6,7,8,"9+"]

        return render(request, 'hearthstone/update-deck.html', {'cards': cardsUser, 'deck': deck, 'cardsUsed' : cardsDeck, 'l' : l, "mana": arr, 'userList': userList})



def mk_paginator(request, items, num_items):
    """Create and return a paginator."""
    paginator = Paginator(items, num_items)
    try: page = int(request.GET.get("page", '1'))
    except ValueError: page = 1

    try:
        items = paginator.page(page)
    except (InvalidPage, EmptyPage):
        items = paginator.page(paginator.num_pages)
    return items

def forum(request):
    """Listing of topics in a forum."""
    topics = Topic.objects.all()
    topics = mk_paginator(request, topics, DJANGO_SIMPLE_FORUM_TOPICS_PER_PAGE)
    userList = User.objects.values()

    if not Forum.objects.all():
        forum = Forum(title="HS Forum", description = "Let's talk !" , creator = request.user)
        forum.save()

    return render(request, 'django_simple_forum/forum.html', {'topics': topics, 'user': request.user, 'pk': 1, 'userList': userList})

def topic(request, topic_id):
    """Listing of posts in a topic."""
    posts = Post.objects.filter(topic=topic_id).order_by("created")
    posts = mk_paginator(request, posts, DJANGO_SIMPLE_FORUM_REPLIES_PER_PAGE)
    topic = Topic.objects.get(pk=topic_id)
    userList = User.objects.values()

    return render(request, 'django_simple_forum/topic.html', {'posts': posts, 'user': request.user, 'pk': topic_id, 'topic':topic, 'userList': userList})

def post_reply(request, topic_id):
    form = PostForm()
    topic = Topic.objects.get(pk=topic_id)
    userList = User.objects.values()
    
    if request.method == 'POST':
        form = PostForm(request.POST)

        if form.is_valid():

            post = Post()
            post.topic = topic
            post.title = form.cleaned_data['title']
            post.body = form.cleaned_data['body']
            post.creator = request.user

            post.save()

            return redirect('forum-detail')

    return render(request, 'django_simple_forum/reply.html', {'form': form, 'user': request.user, 'topic': topic, 'userList': userList})


def new_topic(request, forum_id):
    form = TopicForm()
    forum = Forum.objects.get(pk=forum_id)
    userList = User.objects.values()
    
    if request.method == 'POST':
        form = TopicForm(request.POST)

        if form.is_valid():

            topic = Topic()
            topic.title = form.cleaned_data['title']
            topic.description = form.cleaned_data['description']
            topic.forum = forum
            topic.creator = request.user
            topic.save()
            return redirect('forum-detail')

    return render(request, 'django_simple_forum/new-topic.html', {'form': form, 'user': request.user, 'userList': userList})
