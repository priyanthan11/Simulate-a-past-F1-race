import fastf1
import fastf1.plotting as setup_plt
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from scipy.interpolate import make_interp_spline, interp1d


class TelemetryLoader:
    def __init__(self, year: int, gp_name: str, session_type: str):
        self.year = year
        self.gp_name = gp_name
        self.session_type = session_type
        self.session = None

    def load_session(self):
        self.session = fastf1.get_session(
            self.year, self.gp_name, self.session_type)
        self.session.load()
        return self.session

    def get_track_name(self):
        if self.session:
            return self.session.event['EventName']
        return 'Unknown Track'

    def get_date(self):
        if self.session:
            return self.session.event['EventDate'].strftime("%Y-%m-%d")
        return 'UnKnown Date'


class DriverTelementry:
    def __init__(self, session, driver_code: str):
        self.driver_code = driver_code
        self.session = session

    def extract_fast_lap(self):
        laps = self.session.laps.pick_driver(self.driver_code)
        lap = laps.pick_fastest()
        telementry = lap.get_telemetry()

        return telementry

    def get_lap_number(self):
        if self.session:
            return self.session.laps.pick_driver(self.driver_code).pick_fasted()['LapNumber']


class RaceAnimator:
    def __init__(self, x_data, y_data, speed_data, time_data, driver_name, track_name, date):
        self.x_data = x_data
        self.y_data = y_data
        self.speeds = speed_data
        self.time = time_data
        self.driver_name = driver_name
        self.track_name = track_name
        self.date = date
        self.fig, self.ax = plt.subplots()
        self.point, = self.ax.plot([], [], 'ro', label=self.driver_name)
        # Draw lap path
        self.ax.plot(self.x_data, self.y_data, color='black',
                     linewidth=1, alpha=0.6, label=f"{self.track_name} Track ")
        self.ax.plot([], [], ' ', label=date)
        self.frame_intervals = np.diff(self.time) * 1000  # ms
        self.frame_intervals = np.append(
            self.frame_intervals, self.frame_intervals[-1])  # pad last frame
        self.speed_text = self.ax.text(0.02, 0.95, '', transform=self.ax.transAxes,
                                       fontsize=10, color='blue', bbox=dict(fc='white', ec='blue', lw=1))

    def _init_plot(self):
        self.ax.set_xlim(min(self.x_data), max(self.x_data))
        self.ax.set_ylim(min(self.y_data), max(self.y_data))
        self.ax.set_title(f"{self.driver_name} - {self.track_name} Lap Reply")
        self.ax.legend()
        return (self.point,)

    def _update_plot(self, frame):
        print(
            f"Frame {frame}: x = {self.x_data[frame]}, y = {self.y_data[frame]}")
        self.point.set_data([self.x_data[frame]], [self.y_data[frame]])
        speed = self.speeds[frame]
        self.speed_text.set_text(f"Speed: {speed:.0f} km/h")
        return self.point, self.speed_text

    def animate(self):
        self.current_frame = 0

        def update(_):
            if self.current_frame < len(self.x_data):
                self._update_plot(self.current_frame)
                self.current_frame += 1

                # Delay update only after first frame to avoid index error
                if self.current_frame < len(self.frame_intervals):
                    interaval = self.frame_intervals[self.current_frame]
                    self.anim.event_source.interval = interaval

        self.anim = animation.FuncAnimation(self.fig, update, frames=len(
            self.x_data), init_func=self._init_plot, blit=False)
        plt.show()


def main():
    loader = TelemetryLoader(2024, 'Monaco', 'R')
    session = loader.load_session()
    # change to 'NOR', 'LEC', etc.
    telemetry = DriverTelementry(session, 'VER')
    lap_data = telemetry.extract_fast_lap()

    x = lap_data['X'].to_numpy()
    y = lap_data['Y'].to_numpy()
    speed = lap_data['Speed'].to_numpy()
    time = lap_data['Time'].dt.total_seconds().to_numpy()

    # smooth X and Y
    spline = make_interp_spline(
        np.arange(len(x)), np.column_stack((x, y)), k=2)
    smooth_points = spline(np.linspace(0, len(x) - 1, num=len(x)*10))
    x_smooth, y_smooth = smooth_points[:, 0], smooth_points[:, 1]

    # smooth speed and time to match frame count
    def interpolate_array(arr, new_len):
        interp = interp1d(np.linspace(0, 1, num=len(arr)), arr)
        return interp(np.linspace(0, 1, num=new_len))

    speed_smooth = interpolate_array(speed, len(x_smooth))
    time_smooth = interpolate_array(time, len(x_smooth))

    track_name = loader.get_track_name()
    date = loader.get_date()

    animator = RaceAnimator(x, y, speed,
                            time, 'Verstappen', track_name, date)
    animator.animate()
