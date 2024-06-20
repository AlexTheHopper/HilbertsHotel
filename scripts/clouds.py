import random

class Cloud:
    def __init__(self, pos, img, speed, depth):
        self.pos = list(pos)
        self.img = img
        self.speed = speed
        self.depth = depth


    def update(self):
        self.pos[0] += self.speed


    def render(self, surface, offset = (0, 0)):
        looped_posx = self.pos[0] % (surface.get_width() + self.img.get_width()) - self.img.get_width()
        looped_posy = self.pos[1] % (surface.get_height() + self.img.get_height()) - self.img.get_height()
        surface.blit(self.img, (looped_posx, looped_posy))


class Clouds:
    def __init__(self, cloud_images, count = 16):
        self.clouds = []
        for _ in range(count):
            newCloudX = random.random() * 1080
            newCloudY = random.random() * 360
            newCloudImg = random.choice(cloud_images)
            newCloudSpeed = random.random() * 0.1 + 0.05
            newCloudDepth = random.random() * 0.6 + 0.2

            newCloud = Cloud((newCloudX, newCloudY), newCloudImg, newCloudSpeed, newCloudDepth)
            self.clouds.append(newCloud)

        self.clouds.sort(key=lambda x: x.depth)


    def update(self):
        for cloud in self.clouds:
            cloud.update()
            

    def render(self, surface, offset = (0, 0)):
        for cloud in self.clouds:
            cloud.render(surface, offset = offset)