import pygame
import os
import random

pygame.font.init()
pygame.mixer.init(44100, -16, 2, 2048)
pygame.mixer.set_num_channels(64)

width = 1000
height = 650
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("New Space Invaders")

# Load images
alien_1 = pygame.image.load(os.path.join("PNGS", "marciano_1.png"))
alien_2 = pygame.image.load(os.path.join("PNGS", "marciano_2.png"))
alien_3 = pygame.image.load(os.path.join("PNGS", "marciano_3.png"))

ast_big = pygame.image.load(os.path.join("PNGS", "asteroide_1.png"))
ast_little = pygame.image.load(os.path.join("PNGS", "asteroide_2.png"))
ast_medium = pygame.image.load(os.path.join("PNGS", "asteroide_3.png"))

# Player ship
principal_ship = pygame.image.load(os.path.join("PNGS", "nave_principal.png"))

# Lasers
laser_red = pygame.image.load(os.path.join("PNGS", "bala_roja.png"))
laser_green = pygame.image.load(os.path.join("PNGS", "bala_verde.png"))

# Sound
player_laser_sound = pygame.mixer.Sound("laser_1.wav")
enemy_laser_sound = pygame.mixer.Sound("laser_2.wav")
life_lost_sound = pygame.mixer.Sound("lose_life.wav")
level_up_sound = pygame.mixer.Sound("level_up.wav")

player_laser_sound.set_volume(0.1)
enemy_laser_sound.set_volume(0.5)
life_lost_sound.set_volume(3)
level_up_sound.set_volume(0.8)


# Background
background = pygame.image.load(os.path.join("PNGS", "background.png"))
background_2 = pygame.image.load(os.path.join("PNGS", "background_2.png"))
background_height = background.get_height()
background_rect = background.get_rect()

# Font
font_titles = pygame.font.Font("ChakraPetch-Regular.ttf", 30)
font_menu_options = pygame.font.Font("ChakraPetch-Regular.ttf", 25)
font_big = pygame.font.Font("ChakraPetch-Regular.ttf", 45)
font_big_2 = pygame.font.Font("ChakraPetch-Regular.ttf", 52)
score = 0


# GAME
class Laser:
    def __init__(self, x, y, image):
        self.x = x
        self.y = y
        self.image = image
        self.mask = pygame.mask.from_surface(self.image)

    def draw(self, window):
        window.blit(self.image, (self.x, self.y))

    def move(self, velocity):
        self.y += velocity

    def off_screen(self, height):
        return not (self.y <= height and self.y >= 0)

    def collision(self, obj):
        return collide(self, obj)


class Ship:
    cooldown_constant = 30

    def __init__(self, x, y, health):
        self.x = x
        self.y = y
        self.health = health
        self.ship_img = None
        self.laser_img = None
        self.lasers = []
        self.cool_down_counter = 0

    def draw(self, window):
        # pygame.draw.rect(window, (255, 0, 0), (self.x, self.y, 50, 50))
        window.blit(self.ship_img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(window)

    def move_lasers(self, velocity, obj):
        # Check if the lasers have kicked the player
        self.cooldown()
        for laser in self.lasers:
            laser.move(velocity)
            if laser.off_screen(height):
                self.lasers.remove(laser)
            elif laser.collision(obj):
                obj.health -= 10
                life_lost_sound.play()
                self.lasers.remove(laser)

    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()

    def cooldown(self):
        # Making sure we are not shooting too fast and that we have a second delay before shooting
        if self.cool_down_counter >= self.cooldown_constant:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1

    def shoot(self, player_x):
        # Shooting lasers
        if self.cool_down_counter == 0:
            laser = Laser(player_x + 20, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1


class Player(Ship):
    def __init__(self, x, y, health=100):
        Ship.__init__(self, x, y, health)
        self.ship_img = principal_ship
        self.laser_img = laser_green
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health

    def move_lasers(self, velocity, objs, obj_type):
        # Check if the lasers have kicked an enemy
        global score
        self.cooldown()
        for laser in self.lasers:
            laser.move(velocity)
            if laser.off_screen(height):
                self.lasers.remove(laser)
            else:
                for obj in objs:
                    if laser.collision(obj):
                        objs.remove(obj)
                        if obj_type == "enemy":
                            score += 1
                        # if obj_type == "asteroid":
                            # score += 0
                        if laser in self.lasers:
                            self.lasers.remove(laser)

    def draw(self, window):
        super().draw(window)
        self.health_bar(window)

    def health_bar(self, window):
        pygame.draw.rect(window, (255, 0, 0), (80, 8, 200, 25))
        pygame.draw.rect(window, (124, 218, 70),
                         (80, 8, (200 * (self.health / self.max_health)), 25))


class EnemyShip(Ship):
    enemies_color = {
        "green": (alien_1, laser_red),
        "purple": (alien_2, laser_red),
        "orange": (alien_3, laser_red)}

    def __init__(self, x, y, color, health=100):
        Ship.__init__(self, x, y, health)
        self.ship_img, self.laser_img = self.enemies_color[color]
        self.mask = pygame.mask.from_surface(self.ship_img)

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x + 16, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1
            enemy_laser_sound.play()

    def move(self, velocity):
        self.y += velocity


class Asteroids:
    asteroid_style = {
        "big": ast_big,
        "little": ast_little,
        "medium": ast_medium}

    def __init__(self, x, y, style, health=100):
        super().__init__()
        self.x = x
        self.y = y
        self.ast_img = None
        self.ast_img = self.asteroid_style[style]
        self.health = health
        self.mask = pygame.mask.from_surface(self.ast_img)

    def get_width(self):
        return self.ast_img.get_width()

    def get_height(self):
        return self.ast_img.get_height()

    def move(self, velocity):
        self.y += velocity

    def draw(self, window):
        window.blit(self.ast_img, (self.x, self.y))


def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) is not None


def main_game():
    # Both
    laser_velocity = 4
    # Player
    player_velocity = 8
    player_obj = Player(475, 350)

    # Enemies
    enemies_list = []
    wave_length = 10
    enemy_velocity = 0.5

    asteroid_list = []
    asteroid_length = 2

    run = True
    fps = 60
    lost = False
    lost_count = 0
    level = 0
    global score
    clock = pygame.time.Clock()
    scroll = 0  # Variable para controlar el desplazamiento del fondo
    scroll_velocity = 0

    def background_movement():
        nonlocal scroll  # Acceder a la variable scroll en el alcance exterior

        # Dibujar el fondo repetido
        screen.blit(background, (0, scroll))
        screen.blit(background, (0, scroll - background_height))

        # Desplazar el fondo
        scroll += scroll_velocity  # Velocidad de fondo

        # Reiniciar el desplazamiento
        if scroll >= background_height:
            scroll = 0

    def redraw_window():
        # Draw text
        lives_label = font_titles.render(f"Life: ", True, (255, 255, 255))
        screen.blit(lives_label, (12, 0))

        level_label = font_titles.render(f"LEVEL: {level}", True, (255, 255, 255))
        screen.blit(level_label, (width - level_label.get_width() - 450, 0))

        score_label = font_titles.render(f"Score: {score}", True, (255, 255, 255))
        screen.blit(score_label, (width - score_label.get_width() - 12, 0))

        for enemy in enemies_list:
            enemy.draw(screen)

        for asteroid in asteroid_list:
            asteroid.draw(screen)

        player_obj.draw(screen)

        # Lost message
        if lost:
            lost_label = font_big_2.render("GAME OVER", True, (255, 255, 255))
            screen.blit(lost_label, (width / 2 - lost_label.get_width() / 2, 300))
            your_score_label = font_menu_options.render(f"Your score: {score}", True, (255, 255, 255))
            screen.blit(your_score_label, (width / 2 - your_score_label.get_width() / 2, 370))
            pygame.mixer.music.fadeout(1000)


        pygame.display.update()

    while run:
        clock.tick(fps)
        background_movement()
        redraw_window()

        # Win/Lose
        if player_obj.health <= 0:  # or Player.health <= 0:
            lost = True
            lost_count += 1

        if lost:
            if lost_count > fps * 5:  # Esto es para que espere 5 segundos
                run = False
                # score = 0
                pygame.mixer.music.play(-1)

            else:
                continue

        # Appear enemies and change level
        if len(enemies_list) == 0:  # Cuando ya no haya ningún enemigo en la lista...
            level_up_sound.play()
            level += 1  # Subir nivel
            # wave_length += 2  # aumentar 3 enemigos a la siguiente ola
            enemy_velocity += 0.4
            scroll_velocity += 0.5
            if level >= 3:
                asteroid_length += 2
                for i in range(asteroid_length):
                    asteroid = Asteroids(random.randrange(60, width - 100), random.randrange(-1000, -100),
                                               random.choice(["big", "little", "medium"]))
                    asteroid_list.append(asteroid)

            for i in range(wave_length):
                enemy = EnemyShip(random.randrange(60, width - 100), random.randrange(-1000, -100),
                                  random.choice(["green", "purple", "orange"]))
                enemies_list.append(enemy)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()

        # Move player
        border_constant = 67  # Esta constante solo es para mantener al jugador dentro
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT] and player_obj.x + border_constant < width:
            player_obj.x += player_velocity
        if keys[pygame.K_LEFT] and player_obj.x > 0:
            player_obj.x -= player_velocity
        if keys[pygame.K_UP] and player_obj.y + border_constant > 105:
            player_obj.y -= player_velocity
        if keys[pygame.K_DOWN] and player_obj.y + border_constant < height:
            player_obj.y += player_velocity
        if keys[pygame.K_SPACE]:
            player_obj.shoot(player_obj.x)
            player_laser_sound.play()

        # Move enemies downwards
        for enemy in enemies_list[:]:
            enemy.move(enemy_velocity)
            enemy.move_lasers(laser_velocity, player_obj)

            if random.randrange(0, 2 * fps) == 1:
                enemy.shoot()

            if collide(enemy, player_obj):
                player_obj.health -= 10
                life_lost_sound.play()
                enemies_list.remove(enemy)

            if enemy.y + enemy.get_height() > height:
                player_obj.health -= 10
                life_lost_sound.play()
                enemies_list.remove(enemy)
        player_obj.move_lasers(-laser_velocity, enemies_list, "enemy")

        for asteroid in asteroid_list[:]:
            asteroid.move(enemy_velocity + 0.3)
            if collide(asteroid, player_obj):
                player_obj.health -= 10
                life_lost_sound.play()
                asteroid_list.remove(asteroid)

            if asteroid.y + asteroid.get_height() > height:
                asteroid_list.remove(asteroid)
        player_obj.move_lasers(-laser_velocity, asteroid_list, "asteroid")


def display_menu():
    print("Welcome to Space invaders!")
    print("1. Start Game")
    print("2. View Scores")
    print("3. Credits")
    print("4. Quit")


def start_game():
    player_name = input("Enter your name: ")

    # Código para iniciar el juego
    start_screen()

    # Contador de los puntajes
    global score
    # player_score = score
    with open("scoreboard.txt", "a") as file:
        file.write(player_name + ": " + str(score) + "\n")


def view_scores():
    with open("scoreboard.txt", "r") as file:
        scores = file.readlines()
    if scores:
        print("Scores:")
        for score in scores:
            print(score.strip())
    else:
        print("No scores available.")


def main():
    while True:
        display_menu()
        choice = input("Choose an option (1-4): ")
        if choice == "1":
            start_game()
        elif choice == "2":
            view_scores()
        elif choice == "3":
            print("Credits:\n"
                  "Fernando Bargay Walls\n"
                  "Chantal Alejandra Ferráez Hernández\n"
                  "Emiliano García Mendez")
        elif choice == "4":
            print("Thanks for playing!")
            break
        else:
            print("Invalid choice. Please try again.")


def start_screen():
    pygame.mixer.music.load("princess_peach.wav")
    pygame.mixer.music.set_volume(0.1)
    pygame.mixer.music.play(-1)
    run = True
    while run:

        screen.blit(background_2, (0, 0))
        title_label_1 = font_big_2.render("SPACE", True, (255, 255, 255))
        title_label_2 = font_big_2.render("INVADERS", True, (255, 255, 255))
        instruction = font_titles.render("Press SPACE to begin...", True, (255, 255, 255))

        screen.blit(title_label_1, (50, 200))  # width/2 - title_label_1.get_width()/2
        screen.blit(title_label_2, (50, 240))
        screen.blit(instruction, (50, 370))
        pygame.display.update()
        pygame.display.update()
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if keys[pygame.K_SPACE]:
                main_game()
    pygame.quit()


if __name__ == "__main__":
    main()
