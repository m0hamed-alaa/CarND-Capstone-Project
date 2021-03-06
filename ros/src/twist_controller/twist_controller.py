
from pid import PID
from lowpass import LowPassFilter
from yaw_controller import YawController
import rospy 

GAS_DENSITY = 2.858
ONE_MPH = 0.44704


class Controller(object):
    def __init__(self, wheel_base, steer_ratio, min_speed, max_lat_accel, max_steer_angle , vehicle_mass , wheel_radius , decel_limit):
        # TODO: Implement
        
        self.steering_controller = YawController(wheel_base,steer_ratio,min_speed,max_lat_accel,max_steer_angle)

        kp = 0.3
        ki = 0.1
        kd = 0.1
        mn = 0.0   # minimum throttle value
        mx = 0.2   # maximum throttle value
        self.throttle_controller = PID(kp,ki,kd,mn,mx)

        tau = 0.5  # cutoff frequency = 1/(2*pi*tau)
        ts = 0.02  # sample time
        self.velocity_filter = LowPassFilter(tau,ts)

        self.vehicle_mass = vehicle_mass
        self.wheel_radius = wheel_radius
        self.decel_limit = decel_limit


        self.last_time = rospy.get_time()



    def control(self, linear_velocity, angular_velocity, current_velocity , dbw_enabled):
        
        # Return throttle, brake, steer
        if not dbw_enabled:
        	self.throttle_controller.reset()
        	return 0.0 , 0.0 , 0.0

        
        # filter current velocity
        current_velocity = self.velocity_filter.filt(current_velocity)

        # Throttle control
        velocity_error = linear_velocity - current_velocity
        current_time = rospy.get_time()
        sample_time = current_time - self.last_time
        throttle = self.throttle_controller.step(velocity_error , sample_time)

        # Steering control
        steering = self.steering_controller.get_steering(linear_velocity, angular_velocity, current_velocity)

        # Brake control
        brake = 0.0
        if linear_velocity == 0.0 and current_velocity < 0.1:
        	throttle = 0.0
        	brake = 700      # brake torque in N.m

        elif throttle < 0.1 and velocity_error < 0.0:
        	throttle = 0.0
        	deceleration = max(velocity_error , self.decel_limit)
        	brake = abs(deceleration)*self.vehicle_mass*self.wheel_radius  # brake torque in N.m




        #update last time
        self.last_time = current_time

        return throttle , brake , steering
