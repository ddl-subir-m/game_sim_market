let gameInProgress = false;

let player1Chart, player2Chart;
const player1Data = [];
const player2Data = [];

function initializeCharts() {
    if (player1Chart) {
        player1Chart.destroy();
    }
    if (player2Chart) {
        player2Chart.destroy();
    }
    const ctx1 = document.getElementById('player1Chart');
    const ctx2 = document.getElementById('player2Chart');

    const chartConfig = (playerLabel) => ({
        type: 'scatter',
        data: {
            datasets: [{
                label: `${playerLabel} Actions`,
                data: [],
                backgroundColor: function(context) {
                    if (context.raw && typeof context.raw === 'object') {
                        return context.raw.backgroundColor || (playerLabel === 'Player 1' ? 'rgba(75, 192, 192, 0.6)' : 'rgba(128, 0, 128, 0.6)');
                    }
                    return playerLabel === 'Player 1' ? 'rgba(75, 192, 192, 0.6)' : 'rgba(128, 0, 128, 0.6)';
                },
                borderColor: playerLabel === 'Player 1' ? 'rgba(75, 192, 192, 1)' : 'rgba(128, 0, 128, 1)',
                borderWidth: 1,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: 'linear',
                    position: 'bottom',
                    title: {
                        display: true,
                        text: 'Day'
                    },
                    ticks: {
                        stepSize: 1
                    }
                },
                y: {
                    type: 'category',
                    labels: [],
                    title: {
                        display: true,
                        text: 'Action'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: playerLabel,
                    font: {
                        size: 18
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const point = context.raw;
                            let label = `Day ${point.x}: ${point.y}`;
                            if (point.parameters) {
                                label += ` (${point.parameters.join(', ')})`;
                            }
                            return label;
                        }
                    }
                }
            }
        }
    });

    if (ctx1 && ctx2) {
        player1Chart = new Chart(ctx1, chartConfig('Player 1'));
        player2Chart = new Chart(ctx2, chartConfig('Player 2'));
        console.log('Charts initialized');
    } else {
        console.error('Chart containers not found');
    }
}

function updateCharts(day, player1Action, player2Action) {
    if (player1Chart && player2Chart) {
        console.log(`Updating charts for day ${day}`);
        console.log(`Player 1 action:`, player1Action);
        console.log(`Player 2 action:`, player2Action);

        const player1LastEntry = document.getElementById('player1LogEntries').lastElementChild;
        const player2LastEntry = document.getElementById('player2LogEntries').lastElementChild;

        // Update Player 1's chart
        if (player1Action && player1Action.name) {
            if (!player1Chart.options.scales.y.labels.includes(player1Action.name)) {
                player1Chart.options.scales.y.labels.push(player1Action.name);
            }
            const backgroundColor = player1LastEntry && player1LastEntry.classList.contains('error-message') ? 'red' : 'rgba(75, 192, 192, 0.6)';
            player1Chart.data.datasets[0].data.push({
                x: parseInt(day),
                y: player1Action.name,
                parameters: player1Action.parameters,
                backgroundColor: backgroundColor
            });
        }

        // Update Player 2's chart
        if (player2Action && player2Action.name) {
            if (!player2Chart.options.scales.y.labels.includes(player2Action.name)) {
                player2Chart.options.scales.y.labels.push(player2Action.name);
            }
            const backgroundColor = player2LastEntry && player2LastEntry.classList.contains('error-message') ? 'red' : 'rgba(128, 0, 128, 0.6)';
            player2Chart.data.datasets[0].data.push({
                x: parseInt(day),
                y: player2Action.name,
                parameters: player2Action.parameters,
                backgroundColor: backgroundColor
            });
        }

        console.log('Player 1 Chart data:', player1Chart.data);
        console.log('Player 2 Chart data:', player2Chart.data);

        player1Chart.update();
        player2Chart.update();
    } else {
        console.error('Charts not initialized');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const startGameBtn = document.getElementById('startGame');
    const stopGameBtn = document.getElementById('stopGame');
    const player1LogEntries = document.getElementById('player1LogEntries');
    const player2LogEntries = document.getElementById('player2LogEntries');

    if (!player1LogEntries || !player2LogEntries) {
        console.error('Log entry elements not found. Please check your HTML.');
        return;
    }

    startGameBtn.addEventListener('click', startGame);
    stopGameBtn.addEventListener('click', stopGame);

    async function startGame() {
        if (gameInProgress) return;
        gameInProgress = true;
        startGameBtn.disabled = true;
        stopGameBtn.disabled = false;

        // Reset game state
        const elementsToReset = [
            { id: 'player1LogEntries', property: 'innerHTML' },
            { id: 'player2LogEntries', property: 'innerHTML' },
            { id: 'player1Money', property: 'textContent' },
            { id: 'player1Energy', property: 'textContent' },
            { id: 'player2Money', property: 'textContent' },
            { id: 'player2Energy', property: 'textContent' }
        ];

        elementsToReset.forEach(({ id, property }) => {
            const element = document.getElementById(id);
            if (element) {
                element[property] = property === 'innerHTML' ? '' : '0';
            } else {
                console.warn(`Element with id '${id}' not found.`);
            }
        });

        // Initialize charts
        initializeCharts();

        try {
            const response = await fetch('/start_game', { method: 'POST' });
            gameStream = response.body.getReader();
            const decoder = new TextDecoder();
    
            while (gameInProgress) {
                const { done, value } = await gameStream.read();
                if (done) break;
                
                const jsonString = decoder.decode(value);
                const data = JSON.parse(jsonString);
                
                if (data.game_over) {
                    console.log('Game Over!', data);
                    gameInProgress = false;
                    break;
                } else {
                    console.log(`Day ${data.day} processed`);
                    await updateGameState();
                    updateCharts(data.day, data.player1_action, data.player2_action);
                }
            }
        } catch (error) {
            console.error('Error during game:', error);
        } finally {
            gameInProgress = false;
            startGameBtn.disabled = false;
            stopGameBtn.disabled = true;
            if (gameStream) {
                await gameStream.cancel();
                gameStream = null;
            }
        }
    }

    async function stopGame() {
        if (!gameInProgress) return;
        gameInProgress = false;
        startGameBtn.disabled = false;
        stopGameBtn.disabled = true;
        
        try {
            const response = await fetch('/stop_game', { method: 'POST' });
            if (!response.ok) {
                throw new Error('Failed to stop the game');
            }
            console.log('Game stopped successfully');
            if (gameStream) {
                await gameStream.cancel();
                gameStream = null;
            }
        } catch (error) {
            console.error('Error stopping the game:', error);
        }
    }
    async function updateGameState() {
        const response = await fetch('/game_state');
        const gameState = await response.json();
        
        // Update game info
        const seasonElement = document.getElementById('currentSeason');
        const weatherElement = document.getElementById('currentWeather');
        
        seasonElement.textContent = getSeasonEmoticon(gameState.player1.season);
        weatherElement.textContent = getWeatherEmoticon(gameState.player1.weather);
        
        seasonElement.classList.add('large-emoticon');
        weatherElement.classList.add('large-emoticon');
        
        // Update player farms
        updateFarm('player1', gameState.player1);
        updateFarm('player2', gameState.player2);
        
        // Update player stats
        document.getElementById('player1Money').textContent = gameState.player1.money;
        document.getElementById('player1Energy').textContent = gameState.player1.energy;
        document.getElementById('player2Money').textContent = gameState.player2.money;
        document.getElementById('player2Energy').textContent = gameState.player2.energy;
        
        // Update game log
        player1LogEntries.innerHTML = '';
        player2LogEntries.innerHTML = '';

        gameState.game_log.forEach((entry, index) => {
            const p = document.createElement('p');
            p.textContent = entry;
            
            if (entry.includes("Insufficient") || entry.includes("Invalid") || 
                entry.includes("Unknown") || entry.includes("not ready") || 
                entry.includes("No crop to harvest") || 
                entry.includes("is not vacant")) {
                p.classList.add('error-message');
            } else {
                p.classList.add('success-message');
            }
            
            if (index % 2 === 0) {
                player1LogEntries.appendChild(p);
            } else {
                player2LogEntries.appendChild(p);
            }
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

    // Add these new functions to convert season and weather to emoticons
    function getSeasonEmoticon(season) {
        const seasonEmoticons = {
            'Spring': '🌸🌱',
            'Summer': '☀️🏖️',
            'Fall': '🍂🍁',
            'Winter': '❄️☃️'
        };
        return seasonEmoticons[season] || season;
    }

    function getWeatherEmoticon(weather) {
        const weatherEmoticons = {
            'Sunny': '☀️',
            'Rainy': '🌧️',
            'Drought': '🏜️',
            'Storm': '⛈️'
        };
        return weatherEmoticons[weather] || weather;
    }

});