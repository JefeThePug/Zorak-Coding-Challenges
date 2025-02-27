import pygame
import math

# Initialize Pygame
pygame.init()

# Create a Pygame window
window_size = 600
screen = pygame.display.set_mode((window_size, window_size))

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.prev_x = x
        self.prev_y = y
        self.color = color
        self.velocity_x = 0
        self.velocity_y = 0

    def update(self):
        self.x += self.velocity_x
        self.y += self.velocity_y
        self.velocity_x *= 1
        self.velocity_y *= 1

    def apply_force(self, force_x, force_y):
        self.velocity_x += force_x
        self.velocity_y += force_y

class String:
    def __init__(self, particles):
        self.particles = particles

    def update(self):
        for particle in self.particles:
            particle.update()

        for i in range(len(self.particles) - 1, 0, -1):
            particle1 = self.particles[i]
            particle2 = self.particles[i - 1]
            dx = particle2.x - particle1.x
            dy = particle2.y - particle1.y
            distance = math.sqrt(dx ** 2 + dy ** 2)
            if distance > 10:
                particle1.x = particle2.x - dx / distance * 10
                particle1.y = particle2.y - dy / distance * 10

    def draw(self, screen):
        for particle in self.particles:
            pygame.draw.circle(screen, particle.color, (int(particle.x), int(particle.y)), 5)

# Create a string of particles
colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
particles = [Particle(window_size // 2, window_size // 2, colors[i % len(colors)]) for i in range(20)]
for i in range(1, len(particles)):
    particles[i].x += i * 20
string = String(particles)

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Fill the screen with black
    screen.fill((0, 0, 0))

    # Update and draw the string
    string.update()
    string.draw(screen)

    # Apply a centripetal force to each particle
    for particle in string.particles:
        dx = particle.x - window_size // 2
        dy = particle.y - window_size // 2
        distance = math.sqrt(dx ** 2 + dy ** 2)
        if distance > 0.01:  # add a small tolerance to avoid division by zero
            force_x = -dy / distance * 0.01
            force_y = dx / distance * 0.01
        else:
            force_x = 0
            force_y = 0
        particle.apply_force(force_x, force_y)

    # Update the display
    pygame.display.flip()

    # Cap the frame rate
    pygame.time.delay(1000 // 60)

# Quit Pygame
pygame.quit()