let gameInProgress = false;

document.addEventListener('DOMContentLoaded', () => {
    const startGameBtn = document.getElementById('startGame');
    const stopGameBtn = document.getElementById('stopGame');
    startGameBtn.addEventListener('click', startGame);
    stopGameBtn.addEventListener('click', stopGame);

    async function startGame() {
        if (gameInProgress) return;
        gameInProgress = true;
        startGameBtn.disabled = true;
        stopGameBtn.disabled = false;

        const response = await fetch('/start_game', { method: 'POST' });
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (gameInProgress) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const jsonString = decoder.decode(value);
            const data = JSON.parse(jsonString);
            
            if (data.game_over) {
                console.log('Game Over!', data);
                gameInProgress = false;
                startGameBtn.disabled = false;
                stopGameBtn.disabled = true;
                updateGameState(data);
            } else {
                console.log(`Day ${data.day} processed`);
                document.getElementById('currentDay').textContent = data.day;
                await updateGameState();
            }
        }
    }

    async function stopGame() {
        if (!gameInProgress) return;
        gameInProgress = false;
        startGameBtn.disabled = false;
        stopGameBtn.disabled = true;
        
        // Send a request to the server to stop the game
        await fetch('/stop_game', { method: 'POST' });
    }

    async function updateGameState() {
        const response = await fetch('/game_state');
        const gameState = await response.json();
        
        // Update game info
        document.getElementById('currentDay').textContent = gameState.current_day;
        document.getElementById('currentSeason').textContent = gameState.player1.season;
        document.getElementById('currentWeather').textContent = gameState.player1.weather;
        
        // Update player farms
        updateFarm('player1', gameState.player1);
        updateFarm('player2', gameState.player2);
        
        // Update player stats
        document.getElementById('player1Money').textContent = gameState.player1.money;
        document.getElementById('player1Energy').textContent = gameState.player1.energy;
        document.getElementById('player2Money').textContent = gameState.player2.money;
        document.getElementById('player2Energy').textContent = gameState.player2.energy;
        
        // Update game log
        const logEntries = document.getElementById('logEntries');
        logEntries.innerHTML = '';
        gameState.game_log.forEach(entry => {
            const p = document.createElement('p');
            p.textContent = entry;
            logEntries.appendChild(p);
        });
    }

    function updateFarm(playerId, playerState) {
        const farmElement = document.querySelector(`#${playerId}Farm .plots`);
        farmElement.innerHTML = '';
        playerState.plots.forEach((plot, index) => {
            const plotElement = document.createElement('div');
            plotElement.classList.add('plot');
            plotElement.innerHTML = `
                <p>Plot ${index + 1}</p>
                <p>Soil Quality: ${plot.soil_quality.toFixed(2)}</p>
                ${plot.crop ? `<p>Crop: ${plot.crop.type}</p>
                               <p>Growth: ${(plot.crop.growth_progress * 100).toFixed(2)}%</p>` : '<p>Vacant</p>'}
            `;
            farmElement.appendChild(plotElement);
        });
    }
});