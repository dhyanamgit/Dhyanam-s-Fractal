import math
import queue
import threading
import time

import numpy as np
import pygame

WIDTH, HEIGHT = 900, 650

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Newton Fractal - Smooth Zoom")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 25)

zoom = 1.0
center_x = 0.0
center_y = 0.0

MIN_ZOOM = 0.01
MAX_ZOOM = 1e8
ITERATIONS = 40

PREVIEW_W, PREVIEW_H = 300, 217
FINAL_W, FINAL_H = 900, 650

ROOTS = np.array([
    1 + 0j,
    -0.5 + 0.8660254037844386j,
    -0.5 - 0.8660254037844386j
], dtype=np.complex128)

COLORS = np.array([
    [255, 90, 120],
    [80, 180, 255],
    [255, 210, 80]
], dtype=np.uint8)

jobs = queue.Queue(maxsize=1)
results = queue.Queue(maxsize=1)

state_lock = threading.Lock()
render_id = 0


def get_render_id():
    with state_lock:
        return render_id


def request_render(width, height):
    global render_id

    with state_lock:
        render_id += 1
        number = render_id

        job = (
            number, center_x, center_y, zoom,
            width, height, ITERATIONS
        )

    try:
        jobs.get_nowait()
    except queue.Empty:
        pass

    try:
        jobs.put_nowait(job)
    except queue.Full:
        pass


def calculate_fractal(job):
    number, cx, cy, view_zoom, width, height, iterations = job

    view_width = 3.5 / view_zoom
    view_height = view_width * height / width

    xs = np.linspace(
        cx - view_width / 2,
        cx + view_width / 2,
        width
    )
    ys = np.linspace(
        cy + view_height / 2,
        cy - view_height / 2,
        height
    )

    xx, yy = np.meshgrid(xs, ys)
    z = xx + 1j * yy

    finished = np.zeros(z.shape, dtype=bool)
    root_ids = np.zeros(z.shape, dtype=np.uint8)
    steps = np.zeros(z.shape, dtype=np.uint8)

    extra = max(0, int(math.log10(max(view_zoom, 1.0)) * 4))
    iterations = min(140, iterations + extra)

    for step in range(iterations):
        if step % 2 == 0 and number != get_render_id():
            return None

        active = ~finished
        if not np.any(active):
            break

        values = z[active]
        denominator = 3 * values * values
        safe = np.abs(denominator) > 1e-20

        updated = values.copy()
        updated[safe] = values[safe] - (
            (values[safe] ** 3 - 1) / denominator[safe]
        )
        z[active] = updated

        distances = np.stack(
            [np.abs(z - root) for root in ROOTS],
            axis=0
        )

        nearest = np.argmin(distances, axis=0)
        converged = (
            (~finished)
            & (np.min(distances, axis=0) < 1e-7)
        )

        root_ids[converged] = nearest[converged]
        steps[converged] = min(step, 255)
        finished[converged] = True

    if number != get_render_id():
        return None

    image = np.zeros((height, width, 3), dtype=np.uint8)
    shade = 0.55 + 0.45 * (
        1 - np.minimum(steps.astype(float), 35) / 35
    )

    for i in range(3):
        mask = root_ids == i
        image[mask] = (
            COLORS[i] * shade[mask, None]
        ).astype(np.uint8)

    image[~finished] = (20, 15, 35)

    return image


def render_worker():
    while True:
        job = jobs.get()
        image = calculate_fractal(job)

        if image is None:
            continue

        number = job[0]

        if number != get_render_id():
            continue

        try:
            results.get_nowait()
        except queue.Empty:
            pass

        try:
            results.put_nowait((number, image, job))
        except queue.Full:
            pass


threading.Thread(target=render_worker, daemon=True).start()


def make_surface(array):
    return pygame.surfarray.make_surface(
        np.transpose(array, (1, 0, 2))
    )


def zoom_at(mx, my, factor):
    global zoom, center_x, center_y

    old_width = 3.5 / zoom
    old_height = old_width * HEIGHT / WIDTH

    point_x = center_x + (mx / WIDTH - 0.5) * old_width
    point_y = center_y + (0.5 - my / HEIGHT) * old_height

    zoom = max(MIN_ZOOM, min(MAX_ZOOM, zoom * factor))

    new_width = 3.5 / zoom
    new_height = new_width * HEIGHT / WIDTH

    center_x = point_x - (mx / WIDTH - 0.5) * new_width
    center_y = point_y - (0.5 - my / HEIGHT) * new_height


def draw_button(rect, label):
    pygame.draw.rect(
        screen, (45, 48, 65), rect, border_radius=7
    )
    pygame.draw.rect(
        screen, (150, 155, 180), rect, 2, border_radius=7
    )

    text = font.render(label, True, (255, 255, 255))
    screen.blit(text, text.get_rect(center=rect.center))


plus_button = pygame.Rect(WIDTH - 110, 15, 42, 38)
minus_button = pygame.Rect(WIDTH - 60, 15, 42, 38)
reset_button = pygame.Rect(WIDTH - 165, 15, 45, 38)

image_surface = None

image_x = 0.0
image_y = 0.0
image_zoom = 1.0

dragging = False
last_mouse = None

last_change = time.time()
preview_needed = False
final_needed = False

request_render(PREVIEW_W, PREVIEW_H)

running = True

while running:
    now = time.time()

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            elif event.key in (
                pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS
            ):
                zoom_at(WIDTH / 2, HEIGHT / 2, 1.5)
                last_change = time.time()
                preview_needed = True
                final_needed = True

            elif event.key in (
                pygame.K_MINUS, pygame.K_KP_MINUS
            ):
                zoom_at(WIDTH / 2, HEIGHT / 2, 1 / 1.5)
                last_change = time.time()
                preview_needed = True
                final_needed = True

            elif event.key == pygame.K_r:
                zoom = 1.0
                center_x = 0.0
                center_y = 0.0
                last_change = time.time()
                preview_needed = True
                final_needed = True

        elif event.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()

            zoom_at(mx, my, 1.15 ** event.y)

            last_change = time.time()
            preview_needed = True
            final_needed = True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            if event.button == 1:
                if plus_button.collidepoint(mx, my):
                    zoom_at(WIDTH / 2, HEIGHT / 2, 1.5)

                elif minus_button.collidepoint(mx, my):
                    zoom_at(WIDTH / 2, HEIGHT / 2, 1 / 1.5)

                elif reset_button.collidepoint(mx, my):
                    zoom = 1.0
                    center_x = 0.0
                    center_y = 0.0

                else:
                    zoom_at(mx, my, 1.5)

                last_change = time.time()
                preview_needed = True
                final_needed = True

            elif event.button == 3:
                dragging = True
                last_mouse = event.pos

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3:
                dragging = False
                last_mouse = None
                last_change = time.time()
                preview_needed = True
                final_needed = True

        elif event.type == pygame.MOUSEMOTION and dragging:
            if last_mouse is not None:
                mx, my = event.pos
                old_x, old_y = last_mouse

                view_width = 3.5 / zoom
                view_height = view_width * HEIGHT / WIDTH

                center_x -= (mx - old_x) * view_width / WIDTH
                center_y += (my - old_y) * view_height / HEIGHT

                last_mouse = event.pos
                last_change = time.time()
                preview_needed = True
                final_needed = True

    screen.fill((8, 8, 14))

    if image_surface is not None:
        scale_factor = zoom / image_zoom

        scaled_w = max(1, int(WIDTH * scale_factor))
        scaled_h = max(1, int(HEIGHT * scale_factor))

        old_view_width = 3.5 / image_zoom
        old_view_height = old_view_width * HEIGHT / WIDTH

        new_view_width = 3.5 / zoom
        new_view_height = new_view_width * HEIGHT / WIDTH

        left = WIDTH * (
            0.5 + (image_x - center_x) / new_view_width
            - old_view_width / (2 * new_view_width)
        )

        top = HEIGHT * (
            0.5 - (image_y - center_y) / new_view_height
            - old_view_height / (2 * new_view_height)
        )

        scaled_image = pygame.transform.smoothscale(
            image_surface, (scaled_w, scaled_h)
        )

        screen.blit(scaled_image, (int(left), int(top)))

    if preview_needed and not dragging and now - last_change > 0.06:
        request_render(PREVIEW_W, PREVIEW_H)
        preview_needed = False

    if final_needed and not dragging and now - last_change > 0.35:
        request_render(FINAL_W, FINAL_H)
        final_needed = False

    while True:
        try:
            number, array, job = results.get_nowait()
        except queue.Empty:
            break

        if number == get_render_id():
            image_surface = make_surface(array)
            image_x = job[1]
            image_y = job[2]
            image_zoom = job[3]

    draw_button(plus_button, "+")
    draw_button(minus_button, "-")
    draw_button(reset_button, "R")

    zoom_text = font.render(
        f"Zoom: {zoom:.2f}x", True, (255, 255, 255)
    )
    screen.blit(zoom_text, (15, 20))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
