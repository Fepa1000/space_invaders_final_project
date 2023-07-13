import pygame
import os
import time
import random

pygame.font.init()

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

# Background
background = pygame.image.load(os.path.join("PNGS", "background.png"))
background_height = background.get_height()
background_rect = background.get_rect()

# Font
font_titles = pygame.font.Font("ChakraPetch-Regular.ttf", 30)
font_big = pygame.font.Font("ChakraPetch-Regular.ttf", 70)


class laser_class():
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

    def shoot(self, player_X):
        # Shooting lasers
        if self.cool_down_counter == 0:
            laser = laser_class(player_X + 20, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1


class principal_player(Ship):
    def __init__(self, x, y, health=100):
        Ship.__init__(self, x, y, health)
        self.ship_img = principal_ship
        self.laser_img = laser_green
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health

    def move_lasers(self, velocity, objs):
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
                        score += 1
                        if laser in self.lasers:
                            self.lasers.remove(laser)

    def draw(self, window):
        super().draw(window)
        self.health_bar(window)

    def health_bar(self, window):
        pygame.draw.rect(window, (255, 0, 0), (80, 8, 200, 25))
        pygame.draw.rect(window, (124, 218, 70),
                         (80, 8, (200 * (self.health / self.max_health)), 25))


class enemy_ship(Ship):
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
            laser = laser_class(self.x + 16, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1

    def move(self, velocity):
        self.y += velocity


class asteroids_class():
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


score = 0


def main_game():
    # Both
    laser_velocity = 4
    # Player
    player_velocity = 5
    player_obj = principal_player(475, 350)

    # Enemies
    enemies_list = []
    wave_length = 1
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

        level_label = font_titles.render(f"LEVEL {level}", True, (255, 255, 255))
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
            lost_label = font_big.render("GAME OVER", True, (255, 255, 255))
            screen.blit(lost_label, (width / 2 - lost_label.get_width() / 2, 325))

        pygame.display.update()

    while run:
        clock.tick(fps)
        background_movement()
        redraw_window()

        # Win loose
        if player_obj.health <= 0:  # or principal_player.health <= 0:
            lost = True
            lost_count += 1
        if lost:
            if lost_count > fps * 3:  # Esto es para que espere 5 segundos
                run = False
            else:
                continue
        # Appear enemies and change level
        if len(enemies_list) == 0:  # Cuando ya no haya ningún enemigo en la lista...
            level += 1  # Subir nivel
            wave_length += 2  # aumentar 3 enemigos a la siguiente ola
            enemy_velocity += 0.2
            scroll_velocity += 0.5
            if level >= 3:
                asteroid_length += 2
                for i in range(asteroid_length):
                    asteroid = asteroids_class(random.randrange(60, width - 100), random.randrange(-1000, -100),
                                               random.choice(["big", "little", "medium"]))
                    asteroid_list.append(asteroid)

            for i in range(wave_length):
                enemy = enemy_ship(random.randrange(60, width - 100), random.randrange(-1000, -100),
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

        # Move enemies downwards
        for enemy in enemies_list[:]:
            enemy.move(enemy_velocity)
            enemy.move_lasers(laser_velocity, player_obj)

            if random.randrange(0, 2 * fps) == 1:
                enemy.shoot()

            if collide(enemy, player_obj):
                player_obj.health -= 10
                enemies_list.remove(enemy)

            if enemy.y + enemy.get_height() > height:
                player_obj.health -= 10
                enemies_list.remove(enemy)
        player_obj.move_lasers(-laser_velocity, enemies_list)


        for asteroid in asteroid_list[:]:
            asteroid.move(enemy_velocity + 0.3)
            if collide(asteroid, player_obj):
                player_obj.health -= 10
                asteroid_list.remove(asteroid)

            if asteroid.y + asteroid.get_height() > height:
                asteroid_list.remove(asteroid)
        player_obj.move_lasers(-laser_velocity, asteroid_list)

def main_menu():
    run = True
    while run:
        screen.blit(background, (0,0))
        title_label = font_big.render("SPACE INVADERS", True, (255, 255, 255))
        instruction = font_titles.render("Press SPACE to begin...", True, (255, 255, 255))
        screen.blit(title_label, (width/2 - title_label.get_width()/2, 300))
        screen.blit(instruction, (width / 2 - instruction.get_width() / 2, 400))
        pygame.display.update()
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if keys[pygame.K_SPACE]:
                main_game()
    pygame.quit()


main_menu()
