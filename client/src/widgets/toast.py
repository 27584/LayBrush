from arcade.gui import UILabel


class Toast(UILabel):
    """Label which disappears after a certain time."""

    def __init__(self, text: str, duration: float = 2.0, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.duration = duration
        self.time = 0

    def on_update(self, dt):
        self.time += dt

        if self.time > self.duration:
            self.parent.remove(self)