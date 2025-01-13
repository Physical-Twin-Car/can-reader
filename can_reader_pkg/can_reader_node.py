import can
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32

class CANBusReader(Node):
    def __init__(self):
        super().__init__('canbus_reader')


        # Model auto heeft geen speed en steering sensor dus dit werkt niet op de model auto (ook niet kunnen testen)


        # CAN-interface instellen
        self.bus = can.Bus(interface='socketcan', channel='can0', bitrate=500000)

        # Publishers
        self.speed_pub = self.create_publisher(Float32, '/speed_sensor', 10)
        self.steering_pub = self.create_publisher(Float32, '/steering_sensor', 10)

        # Timer om CAN-berichten te lezen
        self.create_timer(0.04, self.read_can_messages)

    def read_can_messages(self):
        try:
            msg = self.bus.recv(timeout=0.01)  # Ontvang CAN-bericht
            if msg is not None:
                self.process_can_message(msg)
        except Exception as e:
            print(f"Fout bij lezen van CAN: {e}")

    def process_can_message(self, msg):
        if msg.arbitration_id == 0x440:  # Snelheid CAN-ID
            if len(msg.data) >= 2:
                speed_raw = (msg.data[0] << 8 | msg.data[1])
                speed_mps = speed_raw * 0.02778  # Converteer naar m/s (mijn aannamen is dat de speed_raw in Hm/u (hectometer per uur) is.  Niet getest.
                # In het overdrachts document stond een waarde van 0 tot 1000
                self.speed_pub.publish(Float32(data=speed_mps))

        elif msg.arbitration_id == 0x1e5:  # Stuurhoek CAN-ID
            if len(msg.data) >= 3:
                steering_raw = (msg.data[1] << 8 | msg.data[2])
                # stuurhoek data verwerken

                # niet helemaal duidelijk. Uit het overdrachtsdocument gehaald. De maximum waarde van de SteeringSensor is tussen -800 en 800, dus dit lijkt mij niet nodig
                if steering_raw > 32767:
                    steering_raw -= 65536

                # stuurhoek wordt omgerekend naar een hoek in radialen: hoek radialen =  data * (max_hoek_wielen * Pi / 180) / max_stuurwaarde)
                # bij hoek 45 graden naar links (-45) is de waarde -800 en bij een hoek van 45 graden naar rechst (+45) is de waarde 800
                steering_radians = steering_raw * (45.0 * 3.14159 / 180.0) / 800.0
                self.steering_pub.publish(Float32(data=steering_radians))

def main(args=None):
    rclpy.init(args=args)
    node = CANBusReader()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
