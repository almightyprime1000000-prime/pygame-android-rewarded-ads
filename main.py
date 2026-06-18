import pygame
import unity_ads_android as ads

pygame.init()


## Before compiling the game, create the following file:

#src/main/java/com/example/myapp/ShowListenerShim.java

## VS Code:
#code src/main/java/com/example/myapp/ShowListenerShim.java

## Nano:
#nano src/main/java/com/example/myapp/ShowListenerShim.java

## Then copy the contents of ShowListenerShim.java into the newly created file and save it.


WIDTH, HEIGHT = 400, 600
window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)

# Initialize Ads
ads.start_unity_ads(
    game_id="YOUR_GAME_ID",
    ad_unit_id="Rewarded_Android",
    test_mode=True
)

button = pygame.Rect(250, 250, 200, 200)
clock = pygame.time.Clock() # Added to control frame rate

running = True
while running:
    # 1. Handle Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if button.collidepoint(event.pos):
                # Trigger the ad
                ads.show_rewarded("Rewarded_Android")

    # 2. Check for Ad Rewards (Only act if a valid status is returned)
    reward = ads.get_reward()

    if reward: # Make sure 'reward' isn't None or empty
        if reward == "rewarded":
            print("Player earned reward")
            # ADD REWARD CODE HERE (e.g., coins += 100)
            
        elif reward == "skipped":
            print("Player skipped ad")
            
        elif reward == "failed":
            print("Ad failed")
            
        # CRITICAL: If your library doesn't auto-clear the reward,
        # you may need to call a clear function here, like: ads.clear_reward()

    # 3. Drawing/Rendering
    window.fill("white")
    pygame.draw.rect(window, (0, 200, 0), button)
    pygame.display.flip()
    
    clock.tick(60) # Frame rate limiter to prevent CPU maxing out

pygame.quit()