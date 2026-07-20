#!/usr/bin/env python3
import argparse
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


class CmdVelPulse(Node):
    def __init__(self, topic: str) -> None:
        super().__init__("cmd_vel_pulse_test")
        self.publisher = self.create_publisher(Twist, topic, 10)
        self.topic = topic

    def publish_velocity(self, linear_x: float, angular_z: float, duration: float, rate_hz: float) -> None:
        msg = Twist()
        msg.linear.x = linear_x
        msg.angular.z = angular_z

        period = 1.0 / rate_hz
        deadline = time.monotonic() + duration
        while rclpy.ok() and time.monotonic() < deadline:
            self.publisher.publish(msg)
            rclpy.spin_once(self, timeout_sec=0.0)
            time.sleep(period)

    def stop(self, repeats: int = 10) -> None:
        msg = Twist()
        for _ in range(repeats):
            self.publisher.publish(msg)
            rclpy.spin_once(self, timeout_sec=0.0)
            time.sleep(0.05)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish a short /cmd_vel pulse to verify MMK2 base movement.")
    parser.add_argument("--topic", default="/cmd_vel", help="Velocity command topic.")
    parser.add_argument("--linear", type=float, default=0.3, help="Forward speed in m/s.")
    parser.add_argument("--angular", type=float, default=-0.45, help="Yaw speed in rad/s.")
    parser.add_argument("--forward-sec", type=float, default=2.0, help="Forward movement duration.")
    parser.add_argument("--turn-sec", type=float, default=2.0, help="Turn movement duration.")
    parser.add_argument("--rate", type=float, default=20.0, help="Publish rate in Hz.")
    parser.add_argument("--settle-sec", type=float, default=1.0, help="Wait before publishing, for ROS discovery.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rclpy.init()
    node = CmdVelPulse(args.topic)

    try:
        node.get_logger().info(f"Publishing to {args.topic}; waiting {args.settle_sec:.1f}s for discovery")
        time.sleep(args.settle_sec)

        node.get_logger().info(f"Forward: linear.x={args.linear:.3f} for {args.forward_sec:.1f}s")
        node.publish_velocity(args.linear, 0.0, args.forward_sec, args.rate)
        node.stop()

        node.get_logger().info(f"Turn: angular.z={args.angular:.3f} for {args.turn_sec:.1f}s")
        node.publish_velocity(0.0, args.angular, args.turn_sec, args.rate)
        node.stop()

        node.get_logger().info("Movement test complete; robot stopped")
    except KeyboardInterrupt:
        node.get_logger().info("Interrupted; stopping robot")
        node.stop()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()  