var startValue = '0.041', // Your balance must be 10^4 or 10^5 higher than this number. At least.
        stopPercentage = 1, // In %. Reaching this percentage of your balance the script stops. If you dont want it, put "1".
        maxWait = 500, // In milliseconds
        stopped = false,
        stopBefore = 2, // In minutes
        odds = 10,  // Your Payout
        lossMulti = 1.12,  // On Loss Multiply to
        errorCount = 0,
        loseCounter = 0,
        iterations = 0,
        printLog = false;
 
var $loButton = $('#double_your_doge_bet_lo_button'),
                $hiButton = $('#double_your_doge_bet_hi_button');
 
function multiply(){
        var current = $('#double_your_doge_stake').val();
        var multiply = (current * lossMulti).toFixed(8);
        $('#double_your_doge_stake').val(multiply);
}
 
function getRandomWait(){
        var wait = Math.floor(Math.random() * maxWait ) + 100;
 
        if (printLog) {
                console.log('Waiting for ' + wait + 'ms before next bet.');
        }
 
        return wait ;
}
 
function startGame(){
        $('#double_your_doge_payout_multiplier').val(odds);
        console.log('Game started!');
        reset();
        $loButton.trigger('click');
}
 
function stopGame(){
        console.log('Game will stop soon! Let me finish.');
        stopped = true;
}

function resetConsole() {
        console.clear();
        iterations = 0;
}

function toggleLog() {
        printLog = !printLog; 
}
 
function reset(){
        $('#double_your_doge_stake').val(startValue);
}
 
// quick and dirty hack if you have very little bitcoins like 0.0000001
function deexponentize(number){
        return number * 1000000;
}
 
function iHaveEnoughMoni(){
        var balance = deexponentize(parseFloat($('#balance').text()));
        var current = deexponentize($('#double_your_doge_stake').val());

        return (balance * stopPercentage) > current;
}
 
function stopBeforeRedirect(){
        var minutes = parseInt($('title').text());
 
        if( minutes < stopBefore )
        {
                if (printLog) {
                        console.log('Approaching redirect! Stop the game so we don\'t get redirected while loosing.');
                }
                stopGame();
 
                return true;
        }
 
        return false;
}
 
// Unbind old shit
$('#double_your_doge_bet_lose').unbind();
$('#double_your_doge_bet_win').unbind();
 
// Loser
$('#double_your_doge_bet_lose').bind("DOMSubtreeModified",function(event){
        if( $(event.currentTarget).is(':contains("lose")') )
        {
                loseCounter++;
                iterations++;

                if (iterations > 5000) {
                        resetConsole();
                }

                if (printLog) {
                        console.log('You LOST! Multiplying your bet and betting again. Total errors: ' + errorCount);
                }
               
                multiply();

                if ( !iHaveEnoughMoni() ) {
                        console.info('Your bet reached a maximum threshold. Reseting for your safety.')
                        reset();
                        $loButton.trigger('click');
                }
 
                setTimeout(function(){ $loButton.trigger('click'); }, getRandomWait());
 
                //$loButton.trigger('click');
        }
});
 
// Winner
$('#double_your_doge_bet_win').bind("DOMSubtreeModified",function(event){
        if( $(event.currentTarget).is(':contains("win")') )
        {
                iteration++;
                if (iterations > 5000) {
                        resetConsole();
                }

                if( stopBeforeRedirect() )
                {
                        return;
                }

                reset();
                        
                if( stopped )
                {
                        stopped = false;
                        return false;
                }
                if (printLog) {
                        console.log('You WON! After losing ' + loseCounter + ' times. Restarting now!');
                        if (errorCount > 0) {
                                console.error('Total errors: ' + errorCount);
                        }
                }
                
 
                setTimeout(function(){ $loButton.trigger('click'); }, getRandomWait());
        }
});

// Errors
$('#double_your_doge_error').bind("DOMSubtreeModified",function(event) {
        if( $(event.currentTarget).is(':contains("Request timed out")') )
        {
                errorCount++;
                iterations++;

                if (iterations > 5000) {
                        resetConsole();
                }
                console.error('Timed Out message detected. Waiting 3 seconds.');

                if( stopped )
                {
                        stopped = false;
                        return false;
                }

                setTimeout(function(){$loButton.trigger('click');}, 3000);
        }
        else if ( $(event.currentTarget).is(':contains("Insufficient balance")') )
        {
                errorCount++;
                iterations++;

                if (iterations > 5000) {
                        resetConsole();
                }
                console.error('Your bet is higher than your balance. Reanalyze your parameters before starting again. Exiting!')
                
                stopGame();
                return;
        }
        else if ( $(event.currentTarget).length > 3 )
        {
                errorCount++;
                iterations++;

                if (iterations > 5000) {
                        resetConsole();
                }
                console.error('Unknown error detected. Waiting 10 seconds and starting again.');

                if( stopped )
                {
                        stopped = false;
                        return false;
                }

                setTimeout(function(){$loButton.trigger('click');}, 10000);
        }
});
