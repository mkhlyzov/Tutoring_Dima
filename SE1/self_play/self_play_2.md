Question:

I have Java program that acts as a client to a 1v1 game (connects to a server). I created fake engine to test out some strategies in fully offline manner by recreating functionality of the server. Game is basically large field and two players need so search for their gold faster than the opponent. Right now my offline imitation is single player, I want to make it 1v1 (still offline) by making it play versus it self (instance IStrategy::calculateNextMove). I could either hardcode second player into the FakeEngine class (crude but works) or try (I don't know if it is possible though) to turn FakeEngine into local server and connect two copies of ClientMain to it? Which seems more professional but idk if it is even possible.

On the second thought, I decided that I want to turn it into a "local sever" with two copies of the client are being utilized. Can you assist me with rewriting the program? I am interested in how to implement this whole "two copies" and "local server".

Answer:

I'll help you transform your FakeEngine into a local server that can handle two client instances. This is definitely possible and will give you a more realistic test environment. Let me guide you through the implementation.

## Architecture Overview

We'll create:
1. A `LocalGameServer` that manages the game state for both players
2. Modified `FakeNetwork` that connects to this local server
3. A way to run two client instances that communicate through the server

## Implementation

### 1. First, let's create the LocalGameServer class

```java
package network.local;

import messagesbase.UniquePlayerIdentifier;
import messagesbase.messagesfromclient.PlayerHalfMap;
import messagesbase.messagesfromclient.PlayerMove;
import messagesbase.messagesfromserver.EPlayerGameState;
import messagesbase.messagesfromserver.GameState;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

public class LocalGameServer {
    private static LocalGameServer instance;
    
    private final Map<String, GameState> playerGameStates = new ConcurrentHashMap<>();
    private final Map<String, UniquePlayerIdentifier> playerIds = new ConcurrentHashMap<>();
    private final Map<String, PlayerHalfMap> playerHalfMaps = new ConcurrentHashMap<>();
    private final Map<String, Boolean> mapsReceived = new ConcurrentHashMap<>();
    
    private final AtomicInteger playerCounter = new AtomicInteger(0);
    private String gameId = "LOCAL_GAME_" + System.currentTimeMillis();
    
    private GameEngine gameEngine;
    private boolean gameStarted = false;
    
    private LocalGameServer() {
        this.gameEngine = new GameEngine();
    }
    
    public static synchronized LocalGameServer getInstance() {
        if (instance == null) {
            instance = new LocalGameServer();
        }
        return instance;
    }
    
    public ResponseEnvelope<UniquePlayerIdentifier> registerPlayer(String firstName, String lastName, String studentUAccount) {
        String playerIdStr = "Player-" + playerCounter.incrementAndGet();
        UniquePlayerIdentifier playerId = new UniquePlayerIdentifier(playerIdStr);
        
        playerIds.put(playerIdStr, playerId);
        playerGameStates.put(playerIdStr, null);
        mapsReceived.put(playerIdStr, false);
        
        System.out.println("🎮 [Server] Player registered: " + playerIdStr + " (" + studentUAccount + ")");
        
        return ResponseEnvelope.success(playerId);
    }
    
    public ResponseEnvelope<Void> receiveHalfMap(PlayerHalfMap halfMap) {
        String playerId = halfMap.getUniquePlayerID();
        
        if (!playerIds.containsKey(playerId)) {
            return ResponseEnvelope.error("Unknown player");
        }
        
        if (mapsReceived.get(playerId)) {
            return ResponseEnvelope.error("Map already received");
        }
        
        playerHalfMaps.put(playerId, halfMap);
        mapsReceived.put(playerId, true);
        
        System.out.println("🗺️ [Server] Received half map from " + playerId);
        
        // Check if both maps are received
        if (mapsReceived.values().stream().allMatch(received -> received) && mapsReceived.size() == 2) {
            startGame();
        }
        
        return ResponseEnvelope.success(null);
    }
    
    public ResponseEnvelope<Void> receiveMove(PlayerMove move) {
        String playerId = move.getUniquePlayerID();
        
        if (!playerIds.containsKey(playerId)) {
            return ResponseEnvelope.error("Unknown player");
        }
        
        if (!gameStarted) {
            return ResponseEnvelope.error("Game not started yet");
        }
        
        System.out.println("🎯 [Server] Received move from " + playerId + ": " + move.getMove());
        
        // Apply the move in the game engine
        gameEngine.applyMove(playerId, move);
        
        return ResponseEnvelope.success(null);
    }
    
    public ResponseEnvelope<GameState> getGameState(String playerId) {
        if (!playerIds.containsKey(playerId)) {
            return ResponseEnvelope.error("Unknown player");
        }
        
        if (!gameStarted) {
            // Return waiting state
            return ResponseEnvelope.success(createWaitingGameState(playerId));
        }
        
        GameState state = gameEngine.getGameStateForPlayer(playerId);
        playerGameStates.put(playerId, state);
        
        return ResponseEnvelope.success(state);
    }
    
    private void startGame() {
        System.out.println("🚀 [Server] Both maps received. Starting game...");
        
        // Get both half maps
        List<PlayerHalfMap> halfMaps = new ArrayList<>(playerHalfMaps.values());
        
        // Initialize game engine with both half maps
        gameEngine.initializeGame(halfMaps.get(0), halfMaps.get(1));
        gameStarted = true;
        
        System.out.println("✅ [Server] Game started!");
    }
    
    private GameState createWaitingGameState(String playerId) {
        PlayerState waitingPlayer = new PlayerState(
            "Waiting", "Player", "waiting",
            EPlayerGameState.MustWait,
            playerIds.get(playerId),
            false
        );
        
        return new GameState(Set.of(waitingPlayer), gameId);
    }
    
    public boolean isGameStarted() {
        return gameStarted;
    }
    
    // Helper class for responses
    public static class ResponseEnvelope<T> {
        private final ERequestState state;
        private final T data;
        private final String exceptionMessage;
        
        private ResponseEnvelope(ERequestState state, T data, String exceptionMessage) {
            this.state = state;
            this.data = data;
            this.exceptionMessage = exceptionMessage;
        }
        
        public static <T> ResponseEnvelope<T> success(T data) {
            return new ResponseEnvelope<>(ERequestState.Success, data, null);
        }
        
        public static <T> ResponseEnvelope<T> error(String message) {
            return new ResponseEnvelope<>(ERequestState.Error, null, message);
        }
        
        public ERequestState getState() { return state; }
        public Optional<T> getData() { return Optional.ofNullable(data); }
        public String getExceptionMessage() { return exceptionMessage; }
    }
    
    public enum ERequestState {
        Success, Error
    }
}
```

### 2. Create the GameEngine class (enhanced from your FakeEngine)

```java
package network.local;

import messagesbase.UniquePlayerIdentifier;
import messagesbase.messagesfromclient.ETerrain;
import messagesbase.messagesfromclient.PlayerHalfMap;
import messagesbase.messagesfromclient.PlayerHalfMapNode;
import messagesbase.messagesfromclient.PlayerMove;
import messagesbase.messagesfromserver.*;

import java.awt.Point;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

public class GameEngine {
    
    private ETerrain[][] terrainGrid;
    private int width;
    private int height;
    
    private Map<String, PlayerData> players = new ConcurrentHashMap<>();
    private String currentTurn;
    
    private String gameId = "LOCAL_GAME_" + System.currentTimeMillis();
    
    private static class PlayerData {
        String playerId;
        Point position;
        Point fortPosition;
        Point treasurePosition;
        boolean treasureCollected = false;
        boolean treasureObserved = false;
        boolean enemyFortObserved = false;
        EPlayerGameState state = EPlayerGameState.MustWait;
        List<PlayerMove> moveBuffer = new ArrayList<>();
    }
    
    public void initializeGame(PlayerHalfMap halfMap1, PlayerHalfMap halfMap2) {
        // Normalize fort counts
        halfMap1 = normalizeFortCount(halfMap1);
        halfMap2 = normalizeFortCount(halfMap2);
        
        // Shift one map to create a full map
        boolean shiftHorizontally = new Random().nextBoolean();
        PlayerHalfMap shiftedMap = shiftCoordinates(shiftHorizontally ? halfMap2 : halfMap1, shiftHorizontally);
        PlayerHalfMap otherMap = shiftHorizontally ? halfMap1 : halfMap2;
        
        // Create full map
        FullMap fullMap = combineHalfMaps(otherMap, shiftedMap);
        createTerrainArray(fullMap);
        
        // Setup player data
        setupPlayer(halfMap1, otherMap.getUniquePlayerID().equals(halfMap1.getUniquePlayerID()));
        setupPlayer(halfMap2, shiftedMap.getUniquePlayerID().equals(halfMap2.getUniquePlayerID()));
        
        // Determine who starts (random)
        List<String> playerIds = new ArrayList<>(players.keySet());
        currentTurn = playerIds.get(new Random().nextInt(2));
        players.get(currentTurn).state = EPlayerGameState.MustAct;
        
        System.out.println("🎲 [GameEngine] Game initialized. " + currentTurn + " starts.");
    }
    
    private void setupPlayer(PlayerHalfMap halfMap, boolean isPlayer1) {
        PlayerData player = new PlayerData();
        player.playerId = halfMap.getUniquePlayerID();
        
        // Find fort
        PlayerHalfMapNode fort = halfMap.getMapNodes().stream()
                .filter(PlayerHalfMapNode::isFortPresent)
                .findFirst()
                .orElseThrow();
        player.fortPosition = new Point(fort.getX(), fort.getY());
        player.position = new Point(fort.getX(), fort.getY());
        
        // Place treasure near fort
        player.treasurePosition = placeTreasureNearFort(halfMap);
        
        players.put(player.playerId, player);
    }
    
    private Point placeTreasureNearFort(PlayerHalfMap halfMap) {
        PlayerHalfMapNode fort = halfMap.getMapNodes().stream()
                .filter(PlayerHalfMapNode::isFortPresent)
                .findFirst()
                .orElseThrow();
        
        List<PlayerHalfMapNode> candidates = halfMap.getMapNodes().stream()
                .filter(n -> n.getTerrain() == ETerrain.Grass)
                .filter(n -> !n.isFortPresent())
                .toList();
        
        if (candidates.isEmpty()) {
            throw new IllegalStateException("No valid treasure position found");
        }
        
        Random r = new Random();
        PlayerHalfMapNode treasure = candidates.get(r.nextInt(candidates.size()));
        return new Point(treasure.getX(), treasure.getY());
    }
    
    public void applyMove(String playerId, PlayerMove move) {
        if (!playerId.equals(currentTurn)) {
            return; // Not this player's turn
        }
        
        PlayerData player = players.get(playerId);
        PlayerData opponent = players.values().stream()
                .filter(p -> !p.playerId.equals(playerId))
                .findFirst()
                .orElseThrow();
        
        int dx = 0, dy = 0;
        switch(move.getMove()) {
            case Up -> dy = -1;
            case Down -> dy = 1;
            case Left -> dx = -1;
            case Right -> dx = 1;
        }
        
        Point newPos = new Point(player.position.x + dx, player.position.y + dy);
        
        // Check if move is valid
        if (!isInBounds(newPos) || isWater(newPos)) {
            player.state = EPlayerGameState.Lost;
            opponent.state = EPlayerGameState.Won;
            return;
        }
        
        // Update move buffer
        resetBufferIfDirectionChanged(player, move);
        player.moveBuffer.add(move);
        
        int stepsNeeded = calculateStepCost(player.position, newPos);
        if (player.moveBuffer.size() >= stepsNeeded) {
            player.moveBuffer.clear();
            player.position = newPos;
            
            // Update observations
            updateObservations(player);
            
            // Check for win conditions
            if (player.position.equals(player.treasurePosition)) {
                player.treasureCollected = true;
            }
            
            if (player.treasureCollected && player.position.equals(opponent.fortPosition)) {
                player.state = EPlayerGameState.Won;
                opponent.state = EPlayerGameState.Lost;
                return;
            }
            
            // Switch turns
            switchTurn();
        }
    }
    
    private void switchTurn() {
        // Set current player to wait
        players.get(currentTurn).state = EPlayerGameState.MustWait;
        
        // Find opponent and set to act
        for (PlayerData player : players.values()) {
            if (!player.playerId.equals(currentTurn)) {
                currentTurn = player.playerId;
                player.state = EPlayerGameState.MustAct;
                break;
            }
        }
    }
    
    private void updateObservations(PlayerData player) {
        PlayerData opponent = players.values().stream()
                .filter(p -> !p.playerId.equals(player.playerId))
                .findFirst()
                .orElseThrow();
        
        ETerrain currentTerrain = getTerrain(player.position.x, player.position.y);
        
        if (currentTerrain == ETerrain.Mountain) {
            // Check all adjacent tiles
            for (int dx = -1; dx <= 1; dx++) {
                for (int dy = -1; dy <= 1; dy++) {
                    Point neighbor = new Point(player.position.x + dx, player.position.y + dy);
                    if (!isInBounds(neighbor)) continue;
                    
                    if (player.treasurePosition.equals(neighbor)) {
                        player.treasureObserved = true;
                    }
                    if (opponent.fortPosition.equals(neighbor)) {
                        player.enemyFortObserved = true;
                    }
                }
            }
        } else {
            if (player.treasurePosition.equals(player.position)) {
                player.treasureObserved = true;
            }
            if (opponent.fortPosition.equals(player.position)) {
                player.enemyFortObserved = true;
            }
        }
    }
    
    public GameState getGameStateForPlayer(String playerId) {
        PlayerData player = players.get(playerId);
        PlayerData opponent = players.values().stream()
                .filter(p -> !p.playerId.equals(playerId))
                .findFirst()
                .orElse(null);
        
        List<FullMapNode> mapNodes = new ArrayList<>();
        
        for (int x = 0; x < width; x++) {
            for (int y = 0; y < height; y++) {
                Point p = new Point(x, y);
                
                ETerrain terrain = terrainGrid[x][y];
                
                // Determine what this player can see
                ETreasureState treasureState = ETreasureState.NoOrUnknownTreasureState;
                if (player.treasurePosition.equals(p) && !player.treasureCollected && player.treasureObserved) {
                    treasureState = ETreasureState.MyTreasureIsPresent;
                }
                
                EPlayerPositionState positionState = EPlayerPositionState.NoPlayerPresent;
                if (player.position.equals(p)) {
                    positionState = EPlayerPositionState.MyPlayerPosition;
                } else if (opponent != null && opponent.position.equals(p)) {
                    // You can see opponent if on same tile or adjacent?
                    if (player.position.equals(p) || isAdjacent(player.position, opponent.position)) {
                        positionState = EPlayerPositionState.EnemyPlayerPosition;
                    }
                }
                
                EFortState fortState = EFortState.NoOrUnknownFortState;
                if (player.fortPosition.equals(p)) {
                    fortState = EFortState.MyFortPresent;
                } else if (opponent != null && opponent.fortPosition.equals(p) && player.enemyFortObserved) {
                    fortState = EFortState.EnemyFortPresent;
                }
                
                mapNodes.add(new FullMapNode(
                    terrain, positionState, treasureState, fortState, x, y
                ));
            }
        }
        
        FullMap map = new FullMap(mapNodes);
        
        PlayerState playerState = new PlayerState(
            "FirstName", "LastName", "UAccount",
            player.state,
            new UniquePlayerIdentifier(playerId),
            player.treasureCollected
        );
        
        PlayerState opponentState = opponent != null ? 
            new PlayerState(
                "Opponent", "Player", "opponent",
                opponent.state,
                new UniquePlayerIdentifier(opponent.playerId),
                opponent.treasureCollected
            ) : null;
        
        Set<PlayerState> playersSet = opponentState != null ? 
            Set.of(playerState, opponentState) : Set.of(playerState);
        
        return new GameState(map, playersSet, gameId);
    }
    
    // Helper methods (adapted from your FakeEngine)
    private PlayerHalfMap normalizeFortCount(PlayerHalfMap half) {
        List<PlayerHalfMapNode> forts = half.getMapNodes().stream()
                .filter(PlayerHalfMapNode::isFortPresent)
                .toList();
        List<PlayerHalfMapNode> nodes = new ArrayList<>(half.getMapNodes());
        
        Random r = new Random();
        if (!forts.isEmpty()) {
            PlayerHalfMapNode keep = forts.get(r.nextInt(forts.size()));
            
            for (int i = 0; i < nodes.size(); i++) {
                PlayerHalfMapNode n = nodes.get(i);
                if (n.isFortPresent() && !(n.getX() == keep.getX() && n.getY() == keep.getY())) {
                    nodes.set(i, new PlayerHalfMapNode(
                        n.getX(), n.getY(), false, n.getTerrain()
                    ));
                }
            }
        }
        
        return new PlayerHalfMap(half.getUniquePlayerID(), nodes);
    }
    
    private PlayerHalfMap shiftCoordinates(PlayerHalfMap halfMap, boolean shiftHorizontally) {
        List<PlayerHalfMapNode> newNodes = new ArrayList<>();
        int maxX = halfMap.getMapNodes().stream().mapToInt(PlayerHalfMapNode::getX).max().orElse(0);
        int maxY = halfMap.getMapNodes().stream().mapToInt(PlayerHalfMapNode::getY).max().orElse(0);
        
        for (PlayerHalfMapNode node : halfMap.getMapNodes()) {
            if (shiftHorizontally) {
                newNodes.add(new PlayerHalfMapNode(
                    node.getX() + maxX + 1,
                    node.getY(),
                    node.isFortPresent(),
                    node.getTerrain()
                ));
            } else {
                newNodes.add(new PlayerHalfMapNode(
                    node.getX(),
                    node.getY() + maxY + 1,
                    node.isFortPresent(),
                    node.getTerrain()
                ));
            }
        }
        return new PlayerHalfMap(halfMap.getUniquePlayerID(), newNodes);
    }
    
    private FullMap combineHalfMaps(PlayerHalfMap half1, PlayerHalfMap half2) {
        List<PlayerHalfMapNode> combined = new ArrayList<>();
        combined.addAll(half1.getMapNodes());
        combined.addAll(half2.getMapNodes());
        
        List<FullMapNode> fullNodes = new ArrayList<>();
        for (PlayerHalfMapNode node : combined) {
            fullNodes.add(new FullMapNode(
                node.getTerrain(),
                EPlayerPositionState.NoPlayerPresent,
                ETreasureState.NoOrUnknownTreasureState,
                EFortState.NoOrUnknownFortState,
                node.getX(),
                node.getY()
            ));
        }
        
        return new FullMap(fullNodes);
    }
    
    private void createTerrainArray(FullMap fullMap) {
        width = fullMap.getMapNodes().stream()
            .mapToInt(FullMapNode::getX)
            .max()
            .orElse(0) + 1;
        height = fullMap.getMapNodes().stream()
            .mapToInt(FullMapNode::getY)
            .max()
            .orElse(0) + 1;
        
        terrainGrid = new ETerrain[width][height];
        for (FullMapNode node : fullMap.getMapNodes()) {
            terrainGrid[node.getX()][node.getY()] = node.getTerrain();
        }
    }
    
    private ETerrain getTerrain(int x, int y) {
        if (x < 0 || x >= width || y < 0 || y >= height) return null;
        return terrainGrid[x][y];
    }
    
    private boolean isInBounds(Point p) {
        return p.x >= 0 && p.x < width && p.y >= 0 && p.y < height;
    }
    
    private boolean isWater(Point p) {
        ETerrain t = getTerrain(p.x, p.y);
        return t == ETerrain.Water;
    }
    
    private boolean isAdjacent(Point p1, Point p2) {
        return Math.abs(p1.x - p2.x) + Math.abs(p1.y - p2.y) == 1;
    }
    
    private int enterCost(ETerrain t) {
        if (t == null) return 1;
        return switch (t) {
            case Grass -> 1;
            case Mountain -> 2;
            case Water -> 1;
        };
    }
    
    private int leaveCost(ETerrain t) {
        if (t == null) return 1;
        return switch (t) {
            case Grass -> 1;
            case Mountain -> 2;
            case Water -> 9999;
        };
    }
    
    private int calculateStepCost(Point from, Point to) {
        return leaveCost(getTerrain(from.x, from.y)) + enterCost(getTerrain(to.x, to.y));
    }
    
    private void resetBufferIfDirectionChanged(PlayerData player, PlayerMove current) {
        if (!player.moveBuffer.isEmpty()) {
            PlayerMove last = player.moveBuffer.get(player.moveBuffer.size() - 1);
            if (last.getMove() != current.getMove()) {
                player.moveBuffer.clear();
            }
        }
    }
}
```

### 3. Update FakeNetwork to connect to local server

```java
package network;

import network.local.LocalGameServer;
import messagesbase.UniquePlayerIdentifier;
import messagesbase.messagesfromclient.PlayerHalfMap;
import messagesbase.messagesfromclient.PlayerMove;
import messagesbase.messagesfromserver.GameState;

public class FakeNetwork implements INetwork {
    private LocalGameServer server;
    private UniquePlayerIdentifier playerId;
    private long lastPollTime = 0;
    private int GAMESTATE_REQUEST_DELAY;
    
    private String firstName = "Test";
    private String lastName = "Player";
    private String studentUAccount;
    
    public FakeNetwork(int GAMESTATE_REQUEST_DELAY, String studentUAccount) {
        this.GAMESTATE_REQUEST_DELAY = GAMESTATE_REQUEST_DELAY;
        this.studentUAccount = studentUAccount;
        this.server = LocalGameServer.getInstance();
    }
    
    @Override
    public void registerPlayer(String studentUAccount) {
        LocalGameServer.ResponseEnvelope<UniquePlayerIdentifier> response = 
            server.registerPlayer(firstName, lastName, studentUAccount);
        
        if (response.getState() == LocalGameServer.ERequestState.Success) {
            playerId = response.getData().orElse(null);
            System.out.println("✅ [FakeNetwork] Registered as: " + playerId);
        } else {
            System.err.println("❌ [FakeNetwork] Registration failed: " + response.getExceptionMessage());
        }
    }
    
    @Override
    public void sendHalfMap(PlayerHalfMap halfMap) {
        // Ensure the halfmap has our player ID
        PlayerHalfMap mapWithId = new PlayerHalfMap(
            playerId.getUniquePlayerID(),
            halfMap.getMapNodes()
        );
        
        LocalGameServer.ResponseEnvelope<Void> response = server.receiveHalfMap(mapWithId);
        
        if (response.getState() == LocalGameServer.ERequestState.Success) {
            System.out.println("✅ [FakeNetwork] HalfMap sent successfully");
        } else {
            System.err.println("❌ [FakeNetwork] Failed to send HalfMap: " + response.getExceptionMessage());
        }
    }
    
    @Override
    public GameState getGameState() {
        delayForPolling();
        
        if (playerId == null) {
            System.err.println("❌ [FakeNetwork] No player ID available");
            return null;
        }
        
        LocalGameServer.ResponseEnvelope<GameState> response = 
            server.getGameState(playerId.getUniquePlayerID());
        
        if (response.getState() == LocalGameServer.ERequestState.Success) {
            return response.getData().orElse(null);
        } else {
            System.err.println("❌ [FakeNetwork] Failed to get game state: " + response.getExceptionMessage());
            return null;
        }
    }
    
    @Override
    public void sendMove(PlayerMove move) {
        // Ensure the move has our player ID
        PlayerMove moveWithId = new PlayerMove(
            playerId.getUniquePlayerID(),
            move.getMove()
        );
        
        LocalGameServer.ResponseEnvelope<Void> response = server.receiveMove(moveWithId);
        
        if (response.getState() == LocalGameServer.ERequestState.Success) {
            System.out.println("✅ [FakeNetwork] Move sent successfully");
        } else {
            System.err.println("❌ [FakeNetwork] Failed to send move: " + response.getExceptionMessage());
        }
    }
    
    @Override
    public UniquePlayerIdentifier getPlayerId() {
        return playerId;
    }
    
    private void delayForPolling() {
        long now = System.currentTimeMillis();
        
        if (lastPollTime == 0) {
            lastPollTime = now;
            return;
        }
        
        long elapsed = now - lastPollTime;
        long sleepTime = GAMESTATE_REQUEST_DELAY - elapsed;
        
        if (sleepTime > 0) {
            try {
                Thread.sleep(sleepTime);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                System.err.println("Sleep interrupted: " + e.getMessage());
            }
        }
        
        lastPollTime = System.currentTimeMillis();
    }
}
```

### 4. Create a launcher for two clients

```java
package client.main;

import clientcore.ClientMain;
import network.FakeNetwork;

public class LocalGameLauncher {
    
    public static void main(String[] args) {
        System.out.println("🎮 Starting Local 1v1 Game Test");
        System.out.println("=================================");
        
        // Create and start Player 1 in a new thread
        Thread player1Thread = new Thread(() -> {
            try {
                Thread.sleep(100); // Small delay to ensure server is ready
                System.out.println("\n🤖 Starting Player 1...");
                FakeNetwork network1 = new FakeNetwork(200, "player1_account");
                ClientMain player1 = new ClientMain(network1);
                player1.startGame("player1_account");
            } catch (Exception e) {
                System.err.println("❌ Player 1 error: " + e.getMessage());
                e.printStackTrace();
            }
        });
        
        // Create and start Player 2 in a new thread
        Thread player2Thread = new Thread(() -> {
            try {
                Thread.sleep(500); // Slightly longer delay to ensure player 1 registers first
                System.out.println("\n🤖 Starting Player 2...");
                FakeNetwork network2 = new FakeNetwork(200, "player2_account");
                ClientMain player2 = new ClientMain(network2);
                player2.startGame("player2_account");
            } catch (Exception e) {
                System.err.println("❌ Player 2 error: " + e.getMessage());
                e.printStackTrace();
            }
        });
        
        // Start both threads
        player1Thread.start();
        player2Thread.start();
        
        // Wait for both to finish
        try {
            player1Thread.join();
            player2Thread.join();
        } catch (InterruptedException e) {
            System.err.println("Main thread interrupted: " + e.getMessage());
        }
        
        System.out.println("\n🏁 Local Game Test Completed");
    }
    
    // Alternative: Run with different strategies
    public static void runWithStrategies(IStrategy strategy1, IStrategy strategy2) {
        // You'd need to modify ClientMain to accept strategies
        // This is just a placeholder for the concept
    }
}
```

### 5. Update ClientMain to work with the new system

Small modification to your ClientMain to make it work better in multi-threaded environment:

```java
// In startMovePhase(), add a small delay before checking game state
public void startMovePhase() {
    ConsoleView view = new ConsoleView();
    GameHelper gameHelper = new GameHelper(net.getPlayerId());
    
    while (true) {
        // Add a small delay to prevent CPU spinning
        try {
            Thread.sleep(100);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            break;
        }
        
        GameState state = net.getGameState();
        // ... rest of your code
    }
}
```

## How to Use

1. **Run the local game test:**
   ```bash
   java client.main.LocalGameLauncher
   ```

2. **Or run individual clients manually:**
   ```bash
   # Terminal 1
   java client.main.MainClient local 0 player1
   
   # Terminal 2
   java client.main.MainClient local 0 player2
   ```

## Key Benefits

1. **True 1v1 testing** - Both players run independently
2. **Realistic network simulation** - Messages pass through a server
3. **Thread safety** - Concurrent access is handled properly
4. **Test different strategies** - You can easily modify the launcher to use different strategies for each player
5. **No external dependencies** - Everything runs locally

This approach gives you a much more realistic test environment while keeping everything self-contained. The local server manages game state, turn order, and ensures both players see a consistent view of the game.