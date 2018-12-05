from django.http import HttpResponse
import json
import os
from hearthstone.models import Hero, Minion, Card, Spell, Deck, Party, UserCard
from random import randint
from pprint import pprint
from django.shortcuts import render, redirect, get_object_or_404
from django.template import loader
from .forms import UserRegisterForm
from django.contrib import messages
from django.contrib.auth import authenticate, login


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
                
    return render(request, 'hearthstone/index.html')

def home(request):
    title = 'Accueil'
    context = {
        'title': title,
        'parties': Party.objects.all(),
        'Hero': Hero.objects.all(),
    }
    return render(request, 'hearthstone/index.html', context)


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

    return render(request, 'hearthstone/buy-cards.html', {'cards': cards})


def myCards(request):
    cards = UserCard.objects.filter(user_id=request.user.id)
    #Card.objects.all()
    #UserCard.objects.filter(user_id=request.user.id)
    #UserCard.objects.filter(user_id=request.user.id)
    return render(request, 'hearthstone/my-cards.html', {'cards': cards.order_by('cost')})


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


def myDecks(request):
    decksUser = Deck.objects.all().filter(user_id=request.user.id)

    return render(request, 'hearthstone/my-decks.html', {'decks': decksUser})


def deck(request, deck_id):
    deck = get_object_or_404(Deck, pk=deck_id)
    
    #idCards = deck.cards

    cards = Card.objects.filter(deck = deck_id)

    return render(request, 'hearthstone/deck.html', {'cards': cards, 'deck': deck})

def createDeck(request):

    heros = Hero.objects.all()

    return render(request, 'hearthstone/create-deck.html', {'heros': heros})

def createDeckByHero(request, hero_id):

    hero = Hero.objects.get(pk=hero_id)
    #cards = Card.objects.all().filter(playerClass="Druid")  #hero.playerClass
    #cartes = Card.objects.all().filter(playerClass="Druid")  #hero.playerClass
    cardsNeutral = UserCard.objects.filter(user_id=request.user.id).filter(playerClass= "Neutral")
    cardsUser = UserCard.objects.filter(user_id=request.user.id).filter(playerClass=hero.playerClass)
    allCards = cardsUser | cardsNeutral

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

    return render(request, 'hearthstone/create-deck-by-hero.html' , {'cards': allCards.order_by('cost')})


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

        cardsUser = UserCard.objects.filter(user_id=request.user.id)
        cardsDeck = Card.objects.filter(deck = deck_id)

        l = [cD.id for cD in cardsDeck]

        return render(request, 'hearthstone/update-deck.html', {'cards': cardsUser, 'deck': deck, 'cardsUsed' : cardsDeck, 'l' : l})
