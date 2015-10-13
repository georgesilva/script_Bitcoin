var     startValue = '0.00000015', // Your balance must be 10^4 or 10^5 higher than this number. At least.
        stopPercentage = 0.03,  // Reaching this percentage of your balance the script stops. 
                                // If you dont want it, put "2". Recommended "0.08" or lower. 
        maxWait = 300, // In milliseconds
        stopBefore = 2, // In minutes
        odds = 10,  // Your Payout
        lossMulti = 1.14,  // On Loss Multiply to
        
// Dont change these
        inicialBalance = 0,
        stopped = false,
        maxLosses = 0,
        errorCount = 0,
        lossesCounter = 0,
        iterations = 0,
        initTime = 0,
        multiplier = 0,
        printLog = true,
        loseStats = new Array(200),
        sumLosses = 0,
        sumWin = 0;
 
var     $loButton = $('#double_your_btc_bet_lo_button'),
        $hiButton = $('#double_your_btc_bet_hi_button');
 
function multiply(){
        // TODO improvement
        if (lossesCounter > 0 && lossesCounter <= 5)
                multiplier = 1.20;
        else if (lossesCounter > 5)
                multiplier = lossMulti;
        else if (lossesCounter > 64)
                multiplier = multiplier - 0.01;
        else if (lossesCounter > 74)
                multiplier = multiplier - 0.01;


        var current = $('#double_your_btc_stake').val();
        var multiply = (current * multiplier).toFixed(8);
        $('#double_your_btc_stake').val(multiply);
}
 
function getRandomWait(){
        var wait = Math.floor(Math.random() * maxWait ) + 100;
 
        if (printLog) {
                console.log('Waiting for ' + wait + 'ms before next bet.');
        }
 
        return wait ;
}
 
function startGame(){
        jackpotUncheck();
        initiate();
        inicialBalance = parseFloat($('#balance').text());

        $('#double_your_btc_payout_multiplier').val(odds);
        console.log('Game started!');
        reset();
        $loButton.trigger('click');
}
 
function stopGame(){
        console.log('Game will stop soon! Let me finish.');
        stopped = true;
}
 
function reset(){
        multiplier = lossMulti;
        $('#double_your_btc_stake').val(startValue);
}

function initiate() {
        initTime = new Date();
        for (var i = 200; i >= 0; i--) {
                loseStats[i] = 0;
        };
}
 
// quick and dirty hack if you have very little bitcoins like 0.0000001
function deexponentize(number){
        return number * 1000000;
}

function resetConsole() {
        if (iterations > 5000) {
                console.clear();
                iterations = 0;
        }
}

function printStats() {
        var sumTotal = sumWin + sumLosses;
        console.info('Winings: ' + sumWin + ' [' + (sumWin/sumTotal*100).toFixed(2) + '%]. Losses: ' + sumLosses + ' [' + (sumLosses/sumTotal*100).toFixed(2) + '%]. Total: ' + sumTotal);
        var currentBalance = parseFloat($('#balance').text());
        console.info('You Won ' + (currentBalance - inicialBalance).toFixed(9) + ' BTCs. Running for ' + ((new Date().getTime() - initTime.getTime())/60000).toFixed(2) + ' minutes.');
        for (var i = 0; i <= 200; i++) {
                if (loseStats[i] != 0 && typeof(loseStats[i]) !== "undefined")
                        console.log(i + ' => ' + loseStats[i] + ' times.');
        }
}

function toggleLog() {
        printLog = !printLog; 
}

function jackpotUncheck() {
        boxes = $(':input');
        for (var i = 0; i < boxes.length; i++) {
                if (boxes[i].type == 'checkbox') {
                        boxes[i].checked = false;
                }
        }
}
 
function iHaveEnoughMoni(){
        var balance = deexponentize(parseFloat($('#balance').text()));
        var current = deexponentize($('#double_your_btc_stake').val());
 
        return (balance * stopPercentage) > current;
}
 
function stopBeforeRedirect(){
        var minutes = parseInt($('title').text());
 
        if( minutes < stopBefore )
        {
                console.log('Approaching redirect! Stop the game so we don\'t get redirected while loosing.');
                stopGame();
 
                return true;
        }
 
        return false;
}
 
// Unbind old shit
$('#double_your_btc_bet_lose').unbind();
$('#double_your_btc_bet_win').unbind();
 
// Loser
$('#double_your_btc_bet_lose').bind("DOMSubtreeModified",function(event){
        if( $(event.currentTarget).is(':contains("lose")') )
        {
                lossesCounter++;
                iterations++;
                sumLosses++;

                resetConsole();

                if (printLog) {
                        console.log('You LOST! Multiplying your bet and betting again.');
                        if (errorCount > 0) {
                                console.error(' Total errors: ' + errorCount);
                        }
                }
               
                multiply();

                if ( !iHaveEnoughMoni() ) {
                        console.log('Your bet reached a maximum threshold. Reseting for your safety. ' + lossesCounter);
                        reset();
                        
                        if (lossesCounter > maxLosses) {
                                maxLosses = lossesCounter;
                        }
                        console.log('Your maximum number of consecutive losses is ' + maxLosses);
                        if (lossesCounter <= 200)
                                loseStats[lossesCounter]++;
                        lossesCounter = 0;


                        $loButton.trigger('click');
                }
 
                setTimeout(function(){ $loButton.trigger('click'); }, getRandomWait());
 
                //$loButton.trigger('click');
        }
});
 
// Winner
$('#double_your_btc_bet_win').bind("DOMSubtreeModified",function(event){
        if( $(event.currentTarget).is(':contains("win")') )
        {
                iterations++;
                sumWin++;

                resetConsole();

                if( stopBeforeRedirect() )
                {
                        return;
                }

                reset();
                        
                if( stopped )
                {
                        stopped = false;
                        printStats();
                        return false;
                }
                if (lossesCounter > maxLosses) {
                        maxLosses = lossesCounter;
                }
                if (printLog) {
                        console.info('You WON! After losing ' + lossesCounter + ' times. Restarting now!');
                        console.log('Your maximum number of consecutive losses is ' + maxLosses);
                        if (errorCount > 0) {
                                console.error('Total errors: ' + errorCount);
                        }
                }
                
                if (lossesCounter <= 200)
                        loseStats[lossesCounter]++;
                lossesCounter = 0;
                
 
                setTimeout(function(){ $loButton.trigger('click'); }, getRandomWait());
        }
});

// Errors
$('#double_your_btc_error').bind("DOMSubtreeModified",function(event) {
        if( $(event.currentTarget).is(':contains("Request timed out")') )
        {
                errorCount++;
                iterations++;

                resetConsole();
                console.error('Timed Out message detected. Waiting 5 seconds.');
                
                if( stopped )
                {
                        stopped = false;
                        return false;
                }

                setTimeout(function(){$loButton.trigger('click');}, 5000);
        }
        else if ( $(event.currentTarget).is(':contains("Insufficient balance")') )
        {
                errorCount++;
                iterations++;

                resetConsole();
                console.info('Your bet is too high. Reanalyze your parameters before starting again. Exiting!');
                stopGame();
                printStats();
                return;
        }
        else if ( $(event.currentTarget).length > 3 )
        {
                errorCount++;
                iterations++;

                resetConsole();
                console.error('Unknown error detected. Waiting 10 seconds and starting again.');

                if( stopped )
                {
                        stopped = false;
                        return false;
                }

                setTimeout(function(){$loButton.trigger('click');}, 10000);
        }
});
