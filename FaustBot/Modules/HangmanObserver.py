
from FaustBot.Communication.Connection import Connection
from FaustBot.Modules.PrivMsgObserverPrototype import PrivMsgObserverPrototype
from collections import defaultdict
from threading import Lock


class HangmanObserver(PrivMsgObserverPrototype):
    @staticmethod
    def cmd():
        return ['.guess', '.word', '.stop', '.hint', '.score', '.spielregeln']

    @staticmethod
    def help():
        return 'hangman game'

    def __init__(self):
        super().__init__()
        HangmanObserver.lock = Lock()
        self.word = ''
        self.guesses = ['-', '/', ' ', '_']
        self.tries_left = 0
        self.wrong_guessed = []
        self.score = defaultdict(int)
        self.worder = ''
        self.wrongly_guessedWords = []

    def update_on_priv_msg(self, data, connection: Connection):
        if data['message'].find('.guess ') != -1:
            self.guess(data, connection)
            return
        if data['message'].find('.word ') != -1:
            self.take_word(data, connection)
        if data['message'].find('.stop') != -1 and not data['message'].find('.stophunt') != -1:
            connection.send_channel("Spiel gestoppt. Das Wort war: " + self.word)
            self.word = ''
            self.guesses = []
            self.tries_left = 0
            self.wrong_guessed = []
            self.worder = ''
            self.wrongly_guessedWords = []
        if data['message'].find('.hint') != -1:
            self.hint(data, connection)
        if data['message'].find('.score') != -1:
            self.print_score(data, connection)
        if data['message'].find('.spielregeln') != -1:
            self.rules(data, connection)

    def print_score(self, data, connection):
        connection.send_back(data['nick']+" hat einen Score von: " + str(self.score[data['nick']]), data)

    def hint(self, data, connection):
        wrongGuessesString = ""
        if len(self.wrong_guessed) > 0:
            wrongGuessesString += "Falsch geratene Buchstaben bis jetzt: "
            for w in self.wrong_guessed:
                if w == self.wrong_guessed[0]:
                    wrongGuessesString += w
                else:
                    wrongGuessesString += "," + w
        
        # Append wrongly guessed words    
        for w in self.wrongly_guessedWords:
            if w == self.wrongly_guessedWords[0]:
                if len(self.wrong_guessed) > 0:
                    wrongGuessesString += " | "
                wrongGuessesString += "Falsche Wörter: " + w
            else:
                wrongGuessesString += ", " + w
                
        connection.send_back(wrongGuessesString, data)

    def guess(self, data, connection):
        if data['channel'] != connection.details.get_channel():
            connection.send_back("Sorry kein raten im Query", data)
            return
        guess = data['message'].split(' ')[1].upper()
        if self.tries_left < 1:
            connection.send_channel("Flüstere mir ein neues Wort mit .word WORT")
            return
        word_unique_chars = len(set(self.word))
        if guess == self.word:
            score = (word_unique_chars / 10) * self.count_missing_unique()
            self.score[data['nick']] += int(score * 10)
            self.word = ''
            connection.send_channel("Das ist korrekt: " + guess)
            return
        if guess in self.word:
            self.score[data['nick']] += int((word_unique_chars / 20) * 10)
            self.guesses.append(guess)
        else:
            self.tries_left -= 1
            punishment_factor = 1
            if guess in self.guesses:
                punishment_factor = 2
            self.score[data['nick']] -= int((word_unique_chars / 20) * punishment_factor * 10)
            
            # append thread safe wrongly guessed characters and words
            HangmanObserver.lock.acquire()
            try:
                if guess not in self.wrong_guessed:
                    if len(guess) == 1:
                        self.wrong_guessed.append(guess)
                    else:
                        self.wrongly_guessedWords.append(guess)
            finally:
                HangmanObserver.lock.release()        
            
        connection.send_channel(self.prepare_word(data))

    def take_word(self, data, connection):
        if self.word == '':
            log = open('HangmanLog', 'a')
            log.write(data['nick'] + ' ; ' + data['message'].split(' ')[1].upper() + '\n')
            log.close()
            self.word = data['message'].split(' ')[1].upper()
            self.guesses = ['-', '/', ' ', '_']
            self.wrong_guessed = []
            self.tries_left = 11
            self.wrongly_guessedWords = []
            connection.send_back("Danke für das Wort, es ist nun im Spiel!", data)
            connection.send_channel("Das Wort ist von: "+data['nick'])
            self.worder = data['nick']
            connection.send_channel(self.prepare_word(data))
        else:
            connection.send_back("Sorry es läuft bereits ein Wort", data)

    def prepare_word(self, data):
        outWord = ""
        failedChars = 0
        for char in self.word:
            if char in self.guesses:
                outWord += char + " "
            else:
                outWord += "_ "
                failedChars += 1
        if failedChars == 0:
            outWord = "Das ist korrekt: "+self.word
            self.score[data['nick']] += 5
            self.word = ''
            return outWord
        if self.tries_left == 0:
            self.score[self.worder] += 5
            outWord = "Das richtige Wort wäre gewesen:" + self.word
            self.word = ''
            return outWord
        outWord += "Verbleibende Rateversuche: "+str(self.tries_left)
        return outWord

    def count_missing(self):
        missing_chars = 0
        for char in self.word:
            if char not in self.guesses:
                missing_chars += 1
        return missing_chars

    def count_missing_unique(self):
        return len(set(self.word) - set(self.guesses))

    def rules(self, data, connection):
        connection.send_back("""Wort starten mit ".word Wort" im Query mit dem Bot""", data)
        connection.send_back("""Raten mit ".guess Buchstabe" im Channel""", data)
        connection.send_back("""Geraten werden können einzelne Buchstaben oder das ganze Wort.""", data)
        connection.send_back("""Alle dürfen durcheinander raten. Es gibt keine Reihenfolge.""", data)
        connection.send_back("""".hint" gibt alle bereits falsch geratenen Buchstaben aus.""", data)
        connection.send_back("""Bei 2 verbleibenden Versuchen darf nach einem Tipp vom Steller des Wortes gefragt 
        werden.""", data)
        connection.send_back("""Wer ein Wort errät, darf das nächste stellen.""", data)
        connection.send_back("""Wird ein Wort nicht gelöst, darf derjenige, der es gestellt hat, nochmal.""", data)
        connection.send_back("""Zulässig sind alle Wörter, die deutsch oder im deutschen Sprachraum geläufig sind, 
        mit Ausnahme von fsk18 Begriffen (diese dürfen in #autistenchat-fsk18 gespielt werden, sofern kein Thema 
        läuft).""", data)
