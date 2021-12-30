
import pygame
import os
import random
import csv
import button

pygame.init()


SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Shooter')


clock = pygame.time.Clock()
FPS = 60

#définition des variables du jeu
GRAVITY = 0.75
SCROLL_THRESH = 200
ROWS = 16
COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 21
MAX_LEVELS = 3
screen_scroll = 0
bg_scroll = 0
level = 1
start_game = False


#définition des variables des actions du joueur
moving_left = False
moving_right = False
shoot = False
grenade = False
grenade_thrown = False


#télécharge les images
#images des boutons
start_img = pygame.image.load('img/start_btn.png').convert_alpha()
exit_img = pygame.image.load('img/exit_btn.png').convert_alpha()
restart_img = pygame.image.load('img/restart_btn.png').convert_alpha()
#background
bg_img = pygame.image.load('img/bg.jpg').convert_alpha()
#Création de la map 
img_list = []
for x in range(TILE_TYPES):
    img = pygame.image.load(f'Tile/{x}.png')
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    img_list.append(img)

#télécharge les images 
bullet_img = pygame.image.load('img/bullet.png').convert_alpha()
grenade_img = pygame.image.load('grenade1.png').convert_alpha()
health_box_img = pygame.image.load('img/health.png').convert_alpha()
balle_box_img = pygame.image.load('img/ammo_box.png').convert_alpha()
grenade_box_img = pygame.image.load('img/icons/box_canon.png').convert_alpha()
item_boxes = {
    'Health'    : health_box_img,
    'balle'        : balle_box_img,
    'Grenade'    : grenade_box_img
}


#définition des couleurs
BG = (144, 201, 120)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

#définition police de caractères
font = pygame.font.SysFont('Futura', 30)

def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))


def draw_bg():
    screen.fill(BG)
    width = bg_img.get_width()
    for x in range(5):
        screen.blit(bg_img, (width*x, y))


#fonction pour ralancer le niveau
def reset_level():
    enemy_group.empty()
    balle_group.empty()
    grenade_group.empty()
    explosion_group.empty()
    item_box_group.empty()
    decoration_group.empty()
    water_group.empty()
    exit_group.empty()

    #créer des listes de tile vides
    data = []
    for row in range(ROWS):
        r = [-1] * COLS
        data.append(r)

    return data

 


class Soldier(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed, balle, grenades):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.char_type = char_type
        self.speed = speed
        self.balle = balle
        self.start_balle = balle
        self.shoot_cooldown = 0
        self.grenades = grenades
        self.health = 100
        self.max_health = self.health
        self.direction = 1
        self.y = 0
        self.jump = False
        self.in_air = True
        self.flip = False
        self.animation_list = []
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()
        #IA variables
        self.move_counter = 0
        self.vision = pygame.Rect(0, 0, 150, 20)
        self.idling = False
        self.idling_counter = 0
        
        #lance les images pour le joueur
        type_animation = ['Idle', 'Run', 'Jump', 'Death', 'V4']
        for animation in type_animation:
            #relance une liste d'images temporaire
            temp_list = []
            #compte le nombre de fichiers dans le dossier
            num_of_frames = 6
            for i in range(num_of_frames):
                img = pygame.image.load(f'img/{self.char_type}/{animation}/{i}.png').convert_alpha()
                img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
                temp_list.append(img)
            self.animation_list.append(temp_list)

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()


    def update(self):
        self.update_animation()
        self.check_alive()
        #met à jour le cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1


    def move(self, moving_left, moving_right):
        #réinitialise les variables de mouvements
        screen_scroll = 0
        dx = 0
        dy = 0

        #assigne des variables de mouvement s'il bouge vers la gauche ou la droite
        if moving_left:
            dx = -self.speed
            self.flip = True
            self.direction = -1
        if moving_right:
            dx = self.speed
            self.flip = False
            self.direction = 1

        #saut
        if self.jump == True and self.in_air == False:
            self.y = -11
            self.jump = False
            self.in_air = True

        #application de la gravité
        self.y += GRAVITY
        if self.y > 10:
            self.y
        dy += self.y

        #vérifie les collisions
        for tile in world.obstacle_list:
            #vérifie les collisions dans une direction x
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0
                #si l'ia heurte un mur, le faire se retourner
                if self.char_type == 'enemy':
                    self.direction *= -1
                    self.move_counter = 0
            #vérifie les collisions dans une direction y 
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                #vérifie si le personnage est au-dessus du sol ex. saut
                if self.y < 0:
                    self.y = 0
                    dy = tile[1].bottom - self.rect.top
                #vérifie si le personnage est en-dessous du sol ex. chute
                elif self.y >= 0:
                    self.y = 0
                    self.in_air = False
                    dy = tile[1].top - self.rect.bottom


        #vérifie les collisions avec l'eau
        if pygame.sprite.spritecollide(self, water_group, False):
            self.health = 0

        #vérifie les collisions avec les sorties
        level_complete = False
        if pygame.sprite.spritecollide(self, exit_group, False):
            level_complete = True

        #vérifie s'il y a une chute hors de la map
        if self.rect.bottom > SCREEN_HEIGHT:
            self.health = 0


        #vérifie s'il y a une sortie de l'écran
        if self.char_type == 'player':
            if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
                dx = 0

        #met à jour la position du rectangle
        self.rect.x += dx
        self.rect.y += dy

        #met à jour le déroulement de l'écran en fonction de la position du joueur
        if self.char_type == 'player':
            if (self.rect.right > SCREEN_WIDTH - SCROLL_THRESH and bg_scroll < (world.level_length * TILE_SIZE) - SCREEN_WIDTH)\
                or (self.rect.left < SCROLL_THRESH and bg_scroll > abs(dx)):
                self.rect.x -= dx
                screen_scroll = -dx

        return screen_scroll, level_complete

 

    def shoot(self):
        if self.shoot_cooldown == 0 and self.balle > 0:
            self.shoot_cooldown = 20
            bullet = Bullet(self.rect.centerx + (0.75 * self.rect.size[0] * self.direction), self.rect.centery, self.direction)
            balle_group.add(bullet)
            self.update_action(4)
            #réduction des balles
            self.balle -= 1


    def ai(self):
        if self.alive and player.alive:
            if self.idling == False and random.randint(1, 200) == 1:
                self.update_action(0)#0: idle
                self.idling = True
                self.idling_counter = 50
            #vérifie si l'ia est près du joueur
            if self.vision.colliderect(player.rect):
                #arrete de courir et fait face au joueur
                self.update_action(0)#0: idle
                #tir
                self.shoot()
            else:
                if self.idling == False:
                    if self.direction == 1:
                        ai_moving_right = True
                    else:
                        ai_moving_right = False
                    ai_moving_left = not ai_moving_right
                    self.move(ai_moving_left, ai_moving_right)
                    self.update_action(1)#1: run
                    self.move_counter += 1
                    #met à jour la vision de l'ia 
                    self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)

                    if self.move_counter > TILE_SIZE:
                        self.direction *= -1
                        self.move_counter *= -1
                else:
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False

        #défilement
        self.rect.x += screen_scroll


    def update_animation(self):
        #met à jour l'animation
        ANIMATION_COOLDOWN = 100
        #met à jour l'image en fonction de celle actuelle
        self.image = self.animation_list[self.action][self.frame_index]
        #vérifie l'écoulement depuis la mise à jour précédente
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        #si l'animation est épuisée, la réinitialisation revient au début
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 3:
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0

 

    def update_action(self, new_action):
        #vérifie si la nouvelle action est différente de l'ancienne
        if new_action != self.action:
            self.action = new_action
            #met à jour les paramètres d'animation
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

 

    def check_alive(self):
        if self.health <= 0:
            self.health = 0
            self.speed = 0
            self.alive = False
            self.update_action(3)


    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)


class World():
    def __init__(self):
        self.obstacle_list = []

    def process_data(self, data):
        self.level_length = len(data[0])
        #parcourir chaque valeur dans le fichier de données de niveau
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    img = img_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * TILE_SIZE
                    img_rect.y = y * TILE_SIZE
                    tile_data = (img, img_rect)
                    if tile >= 0 and tile <= 8:
                        self.obstacle_list.append(tile_data)
                    elif tile >= 9 and tile <= 10:
                        water = Water(img, x * TILE_SIZE, y * TILE_SIZE)
                        water_group.add(water)
                    elif tile >= 11 and tile <= 14:
                        decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
                        decoration_group.add(decoration)
                    elif tile == 15:#crée le joueur
                        player = Soldier('player', x * TILE_SIZE, y * TILE_SIZE, 1.2, 5, 20, 5)
                        health_bar = HealthBar(10, 10, player.health, player.health)
                    elif tile == 16:#crée les ennemies
                        enemy = Soldier('enemy', x * TILE_SIZE, y * TILE_SIZE, 1.2, 2, 20, 0)
                        enemy_group.add(enemy)
                    elif tile == 17:#crée la barre de munitions
                        item_box = ItemBox('balle', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 18:#crée la barre de grenade
                        item_box = ItemBox('Grenade', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 19:#crée la barre de vie
                        item_box = ItemBox('Health', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 20:#crée la sortie
                        exit = Exit(img, x * TILE_SIZE, y * TILE_SIZE)
                        exit_group.add(exit)

        return player, health_bar


    def draw(self):
        for tile in self.obstacle_list:
            tile[1][0] += screen_scroll
            screen.blit(tile[0], tile[1])


class Decoration(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll


class Water(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll

class Exit(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll


class ItemBox(pygame.sprite.Sprite):
    def __init__(self, item_type, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.item_type = item_type
        self.image = item_boxes[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))


    def update(self):
        #défile
        self.rect.x += screen_scroll
        #vérifie si le joueur a perdu un élément dans la barre
        if pygame.sprite.collide_rect(self, player):
            #vérifie de quelle barre il s'agissait
            if self.item_type == 'Health':
                player.health += 25
                if player.health > player.max_health:
                    player.health = player.max_health
            elif self.item_type == 'balle':
                player.balle += 15
            elif self.item_type == 'Grenade':
                player.grenades += 3
            #enlève l'élément de la barre
            self.kill()


class HealthBar():
    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health

    def draw(self, health):
        #mise à jour avec la nouvelle vie
        self.health = health
        #calcule le ratio de vie
        ratio = self.health / self.max_health
        pygame.draw.rect(screen, BLACK, (self.x - 2, self.y - 2, 154, 24))
        pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
        pygame.draw.rect(screen, GREEN, (self.x, self.y, 150 * ratio, 20))


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 10
        self.image = bullet_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction

    def update(self):
        #mouvement de la balle
        self.rect.x += (self.direction * self.speed) + screen_scroll
        #vérifie si la balle a quitté l'écran
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()
        #vérifie la collision avec le nieveau
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()

        #vérifie la collision avec les joueurs
        if pygame.sprite.spritecollide(player, balle_group, False):
            if player.alive:
                player.health -= 5
                self.kill()
        for enemy in enemy_group:
            if pygame.sprite.spritecollide(enemy, balle_group, False):
                if enemy.alive:
                    enemy.health -= 25
                    self.kill()

 

class Grenade(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.timer = 100
        self.y = -11
        self.speed = 7
        self.image = grenade_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.direction = direction

    def update(self):
        self.y += GRAVITY
        dx = self.direction * self.speed
        dy = self.y

        #vérifie la collision avec le niveau
        for tile in world.obstacle_list:
            #vérifie la collision avec les murs
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                self.direction *= -1
                dx = self.direction * self.speed
            #vérifie la collision dans une direction y
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                self.speed = 0
                #vérifie si au-dessus du sol
                if self.y < 0:
                    self.y = 0
                    dy = tile[1].bottom - self.rect.top
                #vérifie si en-dessous du sol
                elif self.y >= 0:
                    self.y = 0
                    dy = tile[1].top - self.rect.bottom    


        #met à jour la position de la grenade
        self.rect.x += dx + screen_scroll
        self.rect.y += dy

        #lance le minuteur
        self.timer -= 1
        if self.timer <= 0:
            self.kill()
            explosion = Explosion(self.rect.x, self.rect.y, 0.5)
            explosion_group.add(explosion)
            #inflige des dégâts à tout ce qui est proche
            if abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 2 and \
                abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 2:
                player.health -= 50
            for enemy in enemy_group:
                if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE * 2 and \
                    abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE * 2:
                    enemy.health -= 50

 

class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, scale):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        for num in range(1, 6):
            img = pygame.image.load(f'img/explosion/exp{num}.png').convert_alpha()
            img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
            self.images.append(img)
        self.frame_index = 0
        self.image = self.images[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.counter = 0


    def update(self):
        #défile
        self.rect.x += screen_scroll

        EXPLOSION_SPEED = 4
        #met à jour l'animation de l'explosion
        self.counter += 1

        if self.counter >= EXPLOSION_SPEED:
            self.counter = 0
            self.frame_index += 1
            #si l'animation est complète arrête l'explosion
            if self.frame_index >= len(self.images):
                self.kill()
            else:
                self.image = self.images[self.frame_index]

 

#crée des bouttons
start_button = button.Button(SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 - 150, start_img, 1)
exit_button = button.Button(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50, exit_img, 1)
restart_button = button.Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, restart_img, 2)

#crée des groupes d'animations
enemy_group = pygame.sprite.Group()
balle_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

 

#crée une liste vide
world_data = []
for row in range(ROWS):
    r = [-1] * COLS
    world_data.append(r)
#charge les données des niveaux et crée le monde
with open(f'level{level}_data.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for x, row in enumerate(reader):
        for y, tile in enumerate(row):
            world_data[x][y] = int(tile)
world = World()
player, health_bar = world.process_data(world_data)

 

run = True
while run:

    clock.tick(FPS)

    if start_game == False:
        #dessine le menu
        screen.fill(BG)
        #ajoute les boutons
        if start_button.draw(screen):
            start_game = True
        if exit_button.draw(screen):
            run = False
    else:
        #met à jour le fond
        draw_bg()
        #dessine la map
        world.draw()
        #montre la vie du joueur
        health_bar.draw(player.health)
        #montre la balle
        draw_text('balle: ', font, WHITE, 10, 35)
        for x in range(player.balle):
            screen.blit(bullet_img, (90 + (x * 10), 40))
        #montre les grenades
        draw_text('GRENADES: ', font, WHITE, 10, 60)
        for x in range(player.grenades):
            screen.blit(grenade_img, (135 + (x * 15), 60))


        player.update()
        player.draw()

        for enemy in enemy_group:
            enemy.ai()
            enemy.update()
            enemy.draw()

        #met à jour et dessine les groupes
        balle_group.update()
        grenade_group.update()
        explosion_group.update()
        item_box_group.update()
        decoration_group.update()
        water_group.update()
        exit_group.update()
        balle_group.draw(screen)
        grenade_group.draw(screen)
        explosion_group.draw(screen)
        item_box_group.draw(screen)
        decoration_group.draw(screen)
        water_group.draw(screen)
        exit_group.draw(screen)

        #met à jour les actions des joueurs
        if player.alive:
            #tire les balles
            if shoot:
                player.shoot()
            #lance les grenades
            elif grenade and grenade_thrown == False and player.grenades > 0:
                grenade = Grenade(player.rect.centerx + (0.5 * player.rect.size[0] * player.direction),\
                             player.rect.top, player.direction)
                grenade_group.add(grenade)
                #réduit les grenades
                player.grenades -= 1
                grenade_thrown = True
            if player.in_air:
                player.update_action(2)#2: saute
            elif moving_left or moving_right:
                player.update_action(1)#1: courre
            else:
                player.update_action(0)#0: idle
            screen_scroll, level_complete = player.move(moving_left, moving_right)
            bg_scroll -= screen_scroll
            #vérifie si le joueur a complété le niveau
            if level_complete:
                level += 1
                bg_scroll = 0
                world_data = reset_level()
                if level <= MAX_LEVELS:
                    #charge les données du niveau et crée le monde
                    with open(f'level{level}_data.csv', newline='') as csvfile:
                        reader = csv.reader(csvfile, delimiter=',')
                        for x, row in enumerate(reader):
                            for y, tile in enumerate(row):
                                world_data[x][y] = int(tile)
                    world = World()
                    player, health_bar = world.process_data(world_data)    
        else:
            screen_scroll = 0
            if restart_button.draw(screen):
                bg_scroll = 0
                world_data = reset_level()
                #charge les données du niveau et crée le monde
                with open(f'level{level}_data.csv', newline='') as csvfile:
                    reader = csv.reader(csvfile, delimiter=',')
                    for x, row in enumerate(reader):
                        for y, tile in enumerate(row):
                            world_data[x][y] = int(tile)
                world = World()
                player, health_bar = world.process_data(world_data)


    for event in pygame.event.get():
        #quitte le jeu
        if event.type == pygame.QUIT:
            run = False
        #touches du clavier appuyées
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                moving_left = True
            if event.key == pygame.K_d:
                moving_right = True
            if event.key == pygame.K_SPACE:
                shoot = True
            if event.key == pygame.K_e:
                grenade = True
            if event.key == pygame.K_z and player.alive:
                player.jump = True
            if event.key == pygame.K_ESCAPE:
                run = False


        #touches du clavier lachées
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_q:
                moving_left = False
            if event.key == pygame.K_d:
                moving_right = False
            if event.key == pygame.K_SPACE:
                shoot = False
            if event.key == pygame.K_e:
                grenade = False
                grenade_thrown = False


    pygame.display.update()

pygame.quit()