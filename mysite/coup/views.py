# from django.http import HttpResponse
from django.shortcuts import render, redirect
from .models import Player, Card, Deck, Action, Game, CardInstance, ActionHistory, Function
# from django.contrib.auth.mixins import LoginRequiredMixin
from .action import get_initial_action_data, finish_lose_influence
import random

def index(request):
    players = Player.objects.all()
    names = [player.playerName for player in players]
    if len(players) <= 4:
        if request.user.username not in names and request.user.username:
            player = Player(playerName=request.user.username)
            player.save()
        return render(
            request,
            'login_screen.html',
            context={'players': players})
    else:
        return render(
            request,
            'no_more.html')

def startgame(request):
    game = Game(id=1)
    game.initialize()
    game.clearCurrent()
    game.whoseTurn = random.randint(0, 3)
    game.save()
    Deck.objects.all().delete()
    deck = Deck(id=1)
    deck.save()
    deck.build()
    return redirect(showtable)

def showtable(request):
    def get_action():
        prior_action_name, prior_player_name = game.get_prior_action_info()

        if request.user.get_username() == game.currentPlayerName():
            if current_player_coins >= 10:
                actions = Action.objects.filter(name="Coup")
            else:
                actions = Action.objects.filter(coins_required__lte=current_player_coins)

        if request.user.get_username() != game.currentPlayerName():
            if prior_action_name not in (
            'Income', 'Draw', 'Challenge', None) and request.user.get_username() != prior_player_name:
                actions = Action.objects.filter(name__in=['Challenge'])
            else:
                actions = []

        if game.current_player2:
            actions = []

        if request.user.get_username() == game.current_player2 and game.current_action == 'Assassinate':
            actions = Action.objects.filter(name__in=["Lose Influence", "Block"])

        if request.user.get_username() == game.current_player2 and game.current_action in ('Coup', 'Challenge'):
            actions = Action.objects.filter(name__in=["Lose Influence"])

        if request.user.get_username() == game.current_player2 and game.current_action == 'Steal':
            actions = Action.objects.filter(name__in=["Block", "Allow Steal"])
        if not game.current_action:
            try:
                actions = actions.exclude(name__in=['Block'])
            except:
                pass

        return actions

    players = Player.objects.all()
    actionhistory = ActionHistory.objects.all().order_by('-id')[:4]
    game = Game.objects.all()[0]
    cards = []
    current_player_coins = players.get(playerNumber=game.whoseTurn).coins
    actions = get_action()

    for player in players:
        for card in player.hand.all():
            cards.append(card)

    if not game.ck_winner():
        return render(
            request,
            'table.html',
            context={'players': players, 'actions': actions, 'game': game,
                     'current_player_name': game.currentPlayerName(), 'actionhistory': actionhistory, 'cards': cards,
                     'current_player_coins': current_player_coins}
        )
    else:

        return render(
            request,
            'game_over.html',
            context={'players': players, 'actions': actions, 'game': game, 'winner': game.ck_winner()}
        )

def showdeck(request):
    deck = Deck.objects.all()[0]
    cardsremaining = deck.cardsremaining()
    return render(
        request,
        'show_deck.html',
        context={'deck': deck, 'cardsremaining': cardsremaining}
    )

def initialdeal(request):
    game = Game.objects.get(id=80)
    players = Player.objects.all()
    game.initialDeal()
    return render(
        request,
        'table.html',
        context={'players': players}
    )

def shuffle(request):
    deck = Deck.objects.get(id=210)
    # deck=decks[0]
    deck.shuffle()
    deck.save()
    return render(
        request,
        'show_deck.html',
        context={'deck': deck}
    )

def loseinfluence(request):
    if request.method == 'POST':
        finish_lose_influence(request)
        return redirect(showtable)
    else:
        game = Game.objects.all()[0]
        player = game.getPlayerFromPlayerName(game.current_player2)
        return render(request, 'lose_influence.html', {'player': player, 'cards': player.hand.filter(status='D')})

def actions(request):
    get_initial_action_data(request)

    game = Game.objects.all()[0]
    if not game.pending_action:
        game.nextTurn()
        game.clearCurrent()
        game.save()
        return redirect(showtable)
    else:
        get_initial_action_data(request)

        if game.discardRequired():
            player = game.getPlayerFromPlayerName(game.current_player1)
            return render(request, 'discard.html', {'player': player, 'cards': player.hand.all()})

        if game.playerRequired():
            living = []
            players = Player.objects.all()
            for player in players:
                if player.influence() > 0:
                    if game.current_action != 'Steal':
                        living.append(player)
                    elif game.current_action == 'Steal' and player.coins >= 2:
                        living.append(player)
            return render(request, 'player.html', {'players': living})

        return redirect(showtable)
