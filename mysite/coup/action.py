from .models import Player, Card, Deck, Action, Game, CardInstance, ActionHistory


def take_action(request):
    game = Game.objects.all()[0]
    action = Action.objects.get(name=game.current_action)
    player1 = Player.objects.get(playerName=game.current_player1)
    if not ck_turn(request):
        return
    if game.ck_coins():
        return

    game.redoMessage = None
    if game.current_action == "Income":
        player1.addCoins(1)
    elif game.current_action == "Foreign Aid":
        player1.addCoins(2)
    elif game.current_action == "Take 3 coins":
        player1.addCoins(3)
    elif game.current_action == "Steal":
        pass
    elif game.current_action == 'Assassinate':
        if game.current_player2 == game.current_player1:
            return
        else:
            player1.loseCoins(3)
            player1.save()
            game.clearCurrent()
            game.save()
    elif game.current_action == "Draw":

        if not game.discardRequired():
            player1.draw()
            game.redo=True
            game.save()
        else:
            discards = request.POST.getlist('cardnames', None)
            try:
                # game.redoMessage = str(discards)
                game.save()
                game.discard_cards(discards)
                return
            except:
                game.redoMessage = "Could not discard"
                game.redo=True
                game.save()

        game.redoMessage = None
    elif game.current_action == 'Coup':
        if game.current_player2 == game.current_player1:
            return
        else:
            player1.loseCoins(7)
            player1.save()
    elif game.current_action == 'Challenge':  # assassinate and steal??
        pass
    player1.save()
    # if not game.redo:
    actionhistory = ActionHistory(name=action.name, player1=player1.playerName)
    actionhistory.save()
    game.save()
    return


def get_initial_action_data(request):
    if request.method == 'GET':
        getrequest(request)

    if request.method == 'POST':
        game = Game.objects.all()[0]
        playerName2 = request.POST.get('name', None)
        game.current_player2 = playerName2
        game.save()
    take_action(request)
    return


def ck_turn(request):
    game = Game.objects.all()[0]
    playerName = Player.objects.get(playerNumber=game.whoseTurn).playerName
    if request.user.username == playerName:
        game.redo=False
        game.save()
        return True
    else:
        game.redoMessage = ("{} - It's not your turn".format(request.user.username))
        game.redo=False
        game.save()
        return False


def playerRequired():
    game = Game.objects.all()[0]
    if game.current_player2:
        return
    actionName = game.current_action
    action = Action.objects.get(name=actionName)
    return action.player2_required


# def discardRequired():
#     game = Game.objects.all()[0]
#     player = game.getPlayerFromPlayerName(game.current_player1)
#     if player.cardcount() > 2:
#         return game.discardRequired


def getrequest(request):
    playerName1 = request.GET.get('playerName', None)
    actionName = request.GET.get('action', None)
    game = Game.objects.all()[0]
    game.current_player1 = playerName1
    game.current_action = actionName
    game.redo = False
    game.redoMessage = None
    if actionName == 'Draw':
        game.discardRequired = True
    game.save()
    return
