import OpenGL.GL as GL
import OpenGL.GLUT as GLUT
import math
import random
import time
import json
import os

class MultiTargetSniperGame:
    def __init__(self):
        self.width = 800
        self.height = 600
        self.scope_x = self.width // 2
        self.scope_y = self.height // 2
        self.scope_radius = 30
        self.score = 0
        self.ammo = 20
        self.game_over = False
        self.level = 1
        self.speed_increment = 0
        self.targets = self.spawn_targets()
        self.start_time = time.time()
        self.scores_file = "scores.json"
        self.scores = self.load_scores()
        self.last_speed_increase = time.time()
        self.flash_start_time = 0
        self.is_flashing = False
        self.flash_duration = 3
        self.flash_color = (1.0, 1.0, 1.0)

        self.wind_speed = random.uniform(0.5, 2.0)
        self.wind_direction = random.uniform(0, 2 * math.pi)

        # Perfect shot variables
        self.perfect_shot = False
        self.perfect_shot_time = 0
        self.perfect_shot_duration = 2

        # Combo variables
        self.combo = 0
        self.last_shot_time = 0
        self.combo_timeout = 2

        # Recoil variables
        self.recoil_offset_x = 0
        self.recoil_offset_y = 0
        self.recoil_duration = 0.1  
        self.recoil_start_time = 0
        self.recoil_intensity = 10  

    def spawn_targets(self):
        targets = []
        num_targets = 5 + self.level
        for _ in range(num_targets):
            shape = random.choice(['circle', 'square', 'triangle'])
            target = {
                'x': random.randint(100, self.width - 100),
                'y': random.randint(100, self.height - 100),
                'radius': random.randint(20, 40),
                'speed': 2.0 + (self.level * 0.5) + self.speed_increment,
                'direction': random.uniform(0, 2 * math.pi),
                'color': (random.random(), random.random(), random.random()),
                'shape': shape
            }
            targets.append(target)
        return targets

    def draw_scope(self):
        GL.glColor3f(1.0, 1.0, 1.0)
        self.midpoint_circle(self.scope_x + self.recoil_offset_x, self.scope_y + self.recoil_offset_y, self.scope_radius)
        self.midpoint_line(self.scope_x - self.scope_radius + self.recoil_offset_x, self.scope_y + self.recoil_offset_y,
                          self.scope_x + self.scope_radius + self.recoil_offset_x, self.scope_y + self.recoil_offset_y)
        self.midpoint_line(self.scope_x + self.recoil_offset_x, self.scope_y - self.scope_radius + self.recoil_offset_y,
                          self.scope_x + self.recoil_offset_x, self.scope_y + self.scope_radius + self.recoil_offset_y)

    def draw_targets(self):
        for target in self.targets:
            GL.glColor3f(*target['color'])
            if target['shape'] == 'circle':
                self.midpoint_circle(target['x'] + self.recoil_offset_x, target['y'] + self.recoil_offset_y, target['radius'])
            elif target['shape'] == 'square':
                self.midpoint_square(target['x'] + self.recoil_offset_x, target['y'] + self.recoil_offset_y, target['radius'])
            elif target['shape'] == 'triangle':
                self.midpoint_triangle(target['x'] + self.recoil_offset_x, target['y'] + self.recoil_offset_y, target['radius'])

    def midpoint_circle(self, center_x, center_y, radius):
        x = radius
        y = 0
        decision = 1 - radius
        
        GL.glBegin(GL.GL_POINTS)
        self.plot_circle_points(center_x, center_y, x, y)
        
        while y < x:
            y += 1
            if decision <= 0:
                decision += 2 * y + 1
            else:
                x -= 1
                decision += 2 * (y - x) + 1
            
            self.plot_circle_points(center_x, center_y, x, y)
        GL.glEnd()

    def plot_circle_points(self, center_x, center_y, x, y):
        points = [
            (center_x + x, center_y + y), (center_x - x, center_y + y),
            (center_x + x, center_y - y), (center_x - x, center_y - y),
            (center_x + y, center_y + x), (center_x - y, center_y + x),
            (center_x + y, center_y - x), (center_x - y, center_y - x)
        ]
        for px, py in points:
            GL.glVertex2f(px, py)

    def midpoint_square(self, center_x, center_y, size):
        half_size = size // 2

        self.midpoint_line(center_x - half_size, center_y + half_size,
                          center_x + half_size, center_y + half_size)

        self.midpoint_line(center_x - half_size, center_y - half_size,
                          center_x + half_size, center_y - half_size)

        self.midpoint_line(center_x - half_size, center_y - half_size,
                          center_x - half_size, center_y + half_size)

        self.midpoint_line(center_x + half_size, center_y - half_size,
                          center_x + half_size, center_y + half_size)
    
    def midpoint_triangle(self, center_x, center_y, size):
        height = size * math.sqrt(3) / 2

        self.midpoint_line(center_x - size / 2, center_y - height / 2,
                            center_x + size / 2, center_y - height / 2)

        self.midpoint_line(center_x, center_y + height / 2,
                          center_x - size / 2, center_y - height / 2)

        self.midpoint_line(center_x, center_y + height / 2,
                          center_x + size / 2, center_y - height / 2)

    def midpoint_line(self, x1, y1, x2, y2):
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        steep = dy > dx

        if steep:
            x1, y1 = y1, x1
            x2, y2 = y2, x2
            dx, dy = dy, dx

        if x1 > x2:
            x1, x2 = x2, x1
            y1, y2 = y2, y1

        y_step = 1 if y1 < y2 else -1
        decision = 2 * dy - dx
        y = y1

        GL.glBegin(GL.GL_POINTS)
        for x in range(int(x1), int(x2) + 1):
            if steep:
                GL.glVertex2f(y, x)
            else:
                GL.glVertex2f(x, y)
            if decision > 0:
                y += y_step
                decision -= 2 * dx
            decision += 2 * dy
        GL.glEnd()

    def update_targets(self):
        for target in self.targets:
            # Apply wind effect
            target['x'] += math.cos(target['direction']) * (target['speed'] + self.wind_speed * math.cos(self.wind_direction))
            target['y'] += math.sin(target['direction']) * (target['speed'] + self.wind_speed * math.sin(self.wind_direction))
    
            # Bounce off walls
            if target['x'] - target['radius'] < 0 or target['x'] + target['radius'] > self.width:
                target['direction'] = math.pi - target['direction']
            if target['y'] - target['radius'] < 0 or target['y'] + target['radius'] > self.height:
                target['direction'] = -target['direction']

    def shoot(self, x, y):
        if self.ammo <= 0 or self.game_over:
            return

        self.ammo -= 1
        hit = False
        for target in self.targets[:]:
            dx = x - target['x']
            dy = y - target['y']
            distance = math.sqrt(dx * dx + dy * dy)

            if target['shape'] == 'circle' and distance < target['radius']:
                hit = True
            elif target['shape'] == 'square' and self.is_point_in_square(x, y, target['x'], target['y'], target['radius'] * 2):
                hit = True
            elif target['shape'] == 'triangle' and self.is_point_in_triangle(x, y, target['x'], target['y'], target['radius'] * 2):
                hit = True

            if hit:
                self.score += 100
                self.targets.remove(target)
                if distance < 5:
                    self.perfect_shot = True
                    self.perfect_shot_time = time.time()
                current_time = time.time()
                if current_time - self.last_shot_time < self.combo_timeout:
                    self.combo += 1
                else:
                    self.combo = 1
                self.last_shot_time = current_time
                break

        if not hit:
            if self.is_flashing:
                self.game_over = True
                self.save_score()
            else:
                if self.ammo <= 0:
                    self.game_over = True
                    self.save_score()
            self.combo = 0

        if not self.targets:
            self.level += 1
            self.targets = self.spawn_targets()
            self.ammo += 10

        # Trigger recoil
        self.recoil_offset_x = random.uniform(-self.recoil_intensity, self.recoil_intensity)
        self.recoil_offset_y = random.uniform(-self.recoil_intensity, self.recoil_intensity)
        self.recoil_start_time = time.time()

    def is_point_in_square(self, px, py, center_x, center_y, size):
        half_size = size // 2
        return (center_x - half_size <= px <= center_x + half_size and
                center_y - half_size <= py <= center_y + half_size)

    def is_point_in_triangle(self, px, py, center_x, center_y, size):
        height = size * math.sqrt(3) / 2
        x1, y1 = center_x, center_y + height / 2
        x2, y2 = center_x - size / 2, center_y - height / 2
        x3, y3 = center_x + size / 2, center_y - height / 2

        def sign(a, b, c):
            return (a[0] - c[0]) * (b[1] - c[1]) - (b[0] - c[0]) * (a[1] - c[1])

        d1 = sign((px, py), (x1, y1), (x2, y2))
        d2 = sign((px, py), (x2, y2), (x3, y3))
        d3 = sign((px, py), (x3, y3), (x1, y1))

        has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
        has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)

        return not (has_neg and has_pos)

    def save_score(self):
        elapsed_time = time.time() - self.start_time
        score_entry = {
            'index': len(self.scores) + 1,
            'score': self.score,
            'time': round(elapsed_time, 2),
            'level': self.level
        }
        self.scores.append(score_entry)
        with open(self.scores_file, 'w') as f:
            json.dump(self.scores, f, indent=4)

    def load_scores(self):
        if os.path.exists(self.scores_file):
            with open(self.scores_file, 'r') as f:
                scores = json.load(f)
                for entry in scores:
                    if 'level' not in entry:
                        entry['level'] = 1
                return scores
        return []

    def draw_hud(self):
        GL.glColor3f(1.0, 1.0, 1.0)
        GL.glRasterPos2f(10 + self.recoil_offset_x, self.height - 20 + self.recoil_offset_y)
        GLUT.glutBitmapString(GLUT.GLUT_BITMAP_HELVETICA_18, f"Score: {self.score}".encode())
        GL.glRasterPos2f(10 + self.recoil_offset_x, self.height - 40 + self.recoil_offset_y)
        GLUT.glutBitmapString(GLUT.GLUT_BITMAP_HELVETICA_18, f"Ammo: {self.ammo}".encode())
        GL.glRasterPos2f(10 + self.recoil_offset_x, self.height - 60 + self.recoil_offset_y)
        GLUT.glutBitmapString(GLUT.GLUT_BITMAP_HELVETICA_18, f"Level: {self.level}".encode())
        GL.glRasterPos2f(10 + self.recoil_offset_x, self.height - 80 + self.recoil_offset_y)
        GLUT.glutBitmapString(GLUT.GLUT_BITMAP_HELVETICA_18, f"Speed Increment: +{self.speed_increment}".encode())

        if self.perfect_shot and (time.time() - self.perfect_shot_time < self.perfect_shot_duration):
            GL.glColor3f(1.0, 1.0, 0.0)
            GL.glRasterPos2f(self.width // 2 - 50 + self.recoil_offset_x, self.height - 100 + self.recoil_offset_y)
            GLUT.glutBitmapString(GLUT.GLUT_BITMAP_HELVETICA_18, b"Perfect Shot!")
        else:
            self.perfect_shot = False

        if self.combo > 0:
            GL.glColor3f(1.0, 1.0, 0.0)
            GL.glRasterPos2f(self.width // 2 - 30 + self.recoil_offset_x, self.height - 120 + self.recoil_offset_y)
            GLUT.glutBitmapString(GLUT.GLUT_BITMAP_HELVETICA_18, f"Combo: {self.combo}x".encode())

    def display(self):
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        GL.glLoadIdentity()

        if self.is_flashing:
            current_time = time.time()
            if current_time - self.flash_start_time < self.flash_duration:
                if int((current_time - self.flash_start_time) * 10) % 2 == 0:
                    GL.glClearColor(*self.flash_color, 1.0)
                else:
                    GL.glClearColor(0.0, 0.0, 0.0, 1.0)
                GL.glClear(GL.GL_COLOR_BUFFER_BIT)
            else:
                self.is_flashing = False
                GL.glClearColor(0.0, 0.0, 0.0, 1.0)

        self.draw_targets()
        self.draw_scope()
        self.draw_hud()

        if self.game_over:
            GL.glColor3f(1.0, 0.0, 0.0)
            GL.glRasterPos2f(self.width//2 - 100 + self.recoil_offset_x, self.height//2 + self.recoil_offset_y)
            GLUT.glutBitmapString(GLUT.GLUT_BITMAP_HELVETICA_18, f"Game Over! Final Score: {self.score}".encode())
            GL.glRasterPos2f(self.width//2 - 80 + self.recoil_offset_x, self.height//2 - 30 + self.recoil_offset_y)
            GLUT.glutBitmapString(GLUT.GLUT_BITMAP_HELVETICA_18, b"Press R to Restart")

            y_offset = 60
            GL.glColor3f(0.0, 1.0, 0.0)
            for score_entry in self.scores[-5:]:
                GL.glRasterPos2f(self.width//2 - 100 + self.recoil_offset_x, self.height//2 - y_offset + self.recoil_offset_y)
                GLUT.glutBitmapString(GLUT.GLUT_BITMAP_HELVETICA_18, f"Score {score_entry['index']}: {score_entry['score']} (Time: {score_entry['time']}s, Level: {score_entry['level']})".encode())
                y_offset += 20

        GLUT.glutSwapBuffers()

    def update(self):
        if not self.game_over:
            self.update_targets()
            if self.ammo <= 0:
                self.game_over = True
                self.save_score()

            current_time = time.time()
            if current_time - self.last_speed_increase >= 7:
                self.speed_increment += 0.25
                self.last_speed_increase = current_time
                for target in self.targets:
                    target['speed'] += 0.25

            if self.score > 1000 and not self.is_flashing:
                self.is_flashing = True
                self.flash_start_time = time.time()

            # Reduce recoil over time
            if current_time - self.recoil_start_time < self.recoil_duration:
                self.recoil_offset_x *= 0.9
                self.recoil_offset_y *= 0.9
            else:
                self.recoil_offset_x = 0
                self.recoil_offset_y = 0

        GLUT.glutPostRedisplay()

    def mouse(self, button, state, x, y):
        if button == GLUT.GLUT_LEFT_BUTTON and state == GLUT.GLUT_DOWN:
            self.shoot(x, self.height - y)

    def keyboard(self, key, x, y):
        if key == b'r':  # Restart the game
            self.__init__()
        elif key == b'q':  # Quit the game
            GLUT.glutLeaveMainLoop()

    def mouse_motion(self, x, y):
        self.scope_x = x
        self.scope_y = self.height - y

    def reshape(self, width, height):
        GL.glViewport(0, 0, width, height)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glOrtho(0, width, 0, height, -1.0, 1.0)
        GL.glMatrixMode(GL.GL_MODELVIEW)

def main():
    game = MultiTargetSniperGame()

    GLUT.glutInit()
    GLUT.glutInitDisplayMode(GLUT.GLUT_DOUBLE | GLUT.GLUT_RGB)
    GLUT.glutInitWindowSize(game.width, game.height)
    GLUT.glutCreateWindow(b"Multi-Target Sniper Game")

    GL.glClearColor(0.0, 0.0, 0.0, 0.0)
    GL.glPointSize(2.0)

    GLUT.glutDisplayFunc(game.display)
    GLUT.glutKeyboardFunc(game.keyboard)
    GLUT.glutMouseFunc(game.mouse)
    GLUT.glutPassiveMotionFunc(game.mouse_motion)
    GLUT.glutReshapeFunc(game.reshape)

    def update(value):
        game.update()
        GLUT.glutTimerFunc(16, update, 0)

    GLUT.glutTimerFunc(0, update, 0)
    GLUT.glutMainLoop()

if __name__ == "__main__":
    main()