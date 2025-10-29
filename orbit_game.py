import numpy as np
import pygame

display_width = 1512
display_height = 982

black = (0,0,0)
white = (255,255,255)
red = (255,0,0)
green = (0,255,0)
blue = (0,0,255)

class Shuttle():
    def __init__(self,x=0,y=0,vx=0,vy=0,mass=2e6):
        self.initparams = [x,y,vx,vy]
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.mass = mass
        
        self.angle = np.pi/2.
        self.thrust_on = False
        self.rotating = 0

        img = pygame.image.load('fire.png')
        self.fireimg = pygame.transform.scale(img, np.array((1, 599./462))*15)
        
        self.get_orbit_params()
    
    def reset(self):
        self.x = self.initparams[0]
        self.y = self.initparams[1]
        self.vx = self.initparams[2]
        self.vy = self.initparams[3]
        
        self.angle = np.pi/2.
        self.thrust_on = False
        self.rotating = 0

        self.get_orbit_params()

    def thrust(self,toggle):
        self.thrust_on = toggle
    
    def rotate(self,toggle):
        self.rotating = toggle
    
    def get_orbit_params(self):
        global planet_mass,G
        k = G*planet_mass # km^3 s^-2
        
        self.r = np.sqrt(self.x**2 + self.y**2)  # km
        vr = (self.x*self.vx + self.y*self.vy)/self.r # km/s
        rhat = np.array([self.x/self.r,self.y/self.r])
        vt = np.linalg.norm(np.array([self.vx,self.vy])-vr*rhat)
        
        p = self.r**2*vt**2/k # km
        self.eps = (p/k*(vr**2 + (vt-np.sqrt(k/p))**2))**(0.5)
        self.a = p/(1-self.eps**2)

        arg = 1/self.eps*(p/self.r - 1)
        if (arg > 1):
            arg = 1
        elif (arg < -1):
            arg = -1
        self.phi = np.arccos(arg)
        if (vr < 0):
            self.phi *= -1
        
        alpha = np.arctan(self.y/np.abs(self.x))
        if (self.x < 0):
            alpha = np.sign(alpha)*np.pi - alpha
        self.omega = alpha - self.phi
    
    def check_orbit(self,planet_radius):

        if (self.eps > 1) or (self.eps < 0):
            return 2

        if (self.r < planet_radius):
            return 3

        rperi = self.a*(1-self.eps)
        if (rperi < planet_radius):
            return 1
        
        return 0

    def get_accel(self,M):
        anorm = G*M/self.r**2 # km/s^2
        theta = np.abs(np.arctan(self.y/self.x))
        ax = anorm*np.cos(theta)
        ay = anorm*np.sin(theta)
        if (self.x > 0):
            ax *= -1
        if (self.y > 0):
            ay *= -1
        # add thrust
        if self.thrust_on:
            thrust_accel = 1./1e3 # km/s^2
            ax += thrust_accel*np.cos(-self.angle)
            ay += thrust_accel*np.sin(-self.angle)
        return ax,ay
    
    def update(self,M,dt=1/60.,speedup=1):
        if (self.rotating != 0):
            self.angle += self.rotating*0.05
        ax,ay = self.get_accel(M)
        self.vx += ax*dt*speedup # km/s
        self.vy += ay*dt*speedup # km/s
        self.x += self.vx*dt*speedup # km
        self.y += self.vy*dt*speedup # km
        
        self.get_orbit_params()
    
    def draw(self,screen):
        # draw orbit
        r = pygame.Rect(0,0,to_pix_units(2*self.a),to_pix_units(2*self.a*np.sqrt(1-self.eps**2)))
        r.center = to_pix_units(-self.a*self.eps*np.cos(self.omega),-self.a*self.eps*np.sin(self.omega))
        draw_ellipse_angle(screen, red, r, np.degrees(self.omega), width=1)
        
        # draw engine
        if self.thrust_on:
            firepos = to_pix_units(self.x,self.y) - np.array([15*np.cos(self.angle),15*np.sin(self.angle)])
            blitrot(screen,self.fireimg,np.degrees(-1*self.angle)+90,*firepos)

        # draw ship
        sz = 10
        points = np.array([(2*sz*np.cos(self.angle),2*sz*np.sin(self.angle)),
                             (sz*np.cos(self.angle+2*np.pi/3.),sz*np.sin(self.angle+2*np.pi/3.)),
                             (sz*np.cos(self.angle-2*np.pi/3.),sz*np.sin(self.angle-2*np.pi/3.))]) + to_pix_units(self.x,self.y)
        pygame.draw.polygon(screen,blue,points)

def blitrot(screen, image, angle, x, y):
    
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center = image.get_rect(center = (x, y)).center)

    screen.blit(rotated_image,new_rect)

def draw_ellipse_angle(surface, color, rect, angle, width=0):
    target_rect = pygame.Rect(rect)
    shape_surf = pygame.Surface(target_rect.size, pygame.SRCALPHA)
    pygame.draw.ellipse(shape_surf, color, (0, 0, *target_rect.size), width)
    rotated_surf = pygame.transform.rotate(shape_surf, angle)
    surface.blit(rotated_surf, rotated_surf.get_rect(center = target_rect.center))

pix_per_km = 200/40000.
G = 6.674e-20 #km^3 s^-2 kg^-1

def to_pix_units(x,y=None):
    if (y is None):
        return x*pix_per_km
    else:
        return (x*pix_per_km+display_width/2.,display_height/2. - y*pix_per_km)

def to_phys_units(x,y=None):
    if (y is None):
        return x/pix_per_km
    else:
        return (x/(pix_per_km-diplay_width/2.),(display_height/2. - y)/pix_per_km)

def postAlert(screen,text):
    lines = text.split("\n")
    fullRect = None
    font = pygame.font.Font('freesansbold.ttf', 32)
    
    for i,l in enumerate(lines):
        textObj = font.render(l, True, white)
        textRect = textObj.get_rect()
        textRect.center = (display_width // 2, display_height // 4 + textRect.height*i)

        if (fullRect is None):
            fullRect = textRect
        else:
            fullRect = textRect.union(fullRect)

        screen.blit(textObj,textRect)
    
    pygame.draw.rect(screen,red,fullRect.inflate(10,10),3)


###
## Do the game!
###


# initialize the pygame module
pygame.init()
pygame.display.set_caption("Orbiter")
clock = pygame.time.Clock()
fr = 60
speedup = 3000

# windowed
# screen = pygame.display.set_mode((display_width,display_height))
# fullscreen
screen = pygame.display.set_mode((0,0),pygame.FULLSCREEN)

planet_mass = 6e24 # kg
planet_radius = 4500 # km
ship = Shuttle(30000,0,0,2)

# define a variable to control the main loop
running = True
active = True

while running:
    for event in pygame.event.get():
        
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                ship.reset()
                active = True
            elif event.key == pygame.K_q:
                running = False

        if active:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    ship.thrust(True)
                if event.key == pygame.K_RIGHT:
                    ship.rotate(1)
                if event.key == pygame.K_LEFT:
                    ship.rotate(-1)
            
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_UP:
                    ship.thrust(False)
                if ((event.key == pygame.K_RIGHT) or 
                    (event.key == pygame.K_LEFT)):
                    ship.rotate(0)
            
    if active:
        ship.update(planet_mass,speedup=speedup)

        orbit_check = ship.check_orbit(planet_radius)
        if (orbit_check == 2):
            postAlert(screen,"You have left the system\nPress r to reset")
            active = False

    if active:

        screen.fill(black)
        # draw planet
        pygame.draw.circle(screen,white,to_pix_units(0,0),to_pix_units(planet_radius))
        try:
            ship.draw(screen)
        except:
            postAlert(screen,"You have left the system\nPress r to reset")
            active = False

        if (orbit_check == 1):
            postAlert(screen,"Collision course detected!")
        elif (orbit_check == 3):
            postAlert(screen,"Explosion...\nPress r to reset")
            active = False
    
    pygame.display.update()
    clock.tick(60)

pygame.quit()