import math
import serial
import serial.tools.list_ports
import random
import time
import sys
import pickle

class Pool_Matrix:
    """
    Class for the Duration of a pool-testing run.
    """

    sampleNum = 0
    dim = 31
    readFile = None
    arduino = None
    arduinoPort = None

    def setup(self):
        self.arduinoPort = [a.device for a in serial.tools.list_ports.comports() if "USB-SERIAL" in a.description][0]
        self.arduino = serial.Serial(self.arduinoPort,9600)

    def read_inputs(self):
        """
        Should read inputs from either the command line or a GUI
        """
        raise NotImplementedError

    def plus_one(self):
        """
        Increases the sample number by 1.
        """

        if (self.sampleNum < self.dim**2):
            self.sampleNum += 1
            return True
        else:
            return False

    def get_tests(self, cell = None):
        """
        Takes in a cell (sample number) and dim (height or width of grid). Total
        number of samples is dim^2; cell is a number from 1 to dim^2.

        Returns a list of 3 integers corresponding to the 3 tests for which 'cell'
        is part of the testing pool.

        First number corresponds to the row test (number from 1 to dim), second
        number is for col test (from dim+1 to 2*dim), third number is for
        diagonal (wrapping) test (from 2*dim+1 to 3*dim).
        """
        if not cell:
            cell = self.sampleNum

        if (cell % self.dim) >= math.ceil(cell / self.dim):
            return [
                math.ceil(cell / self.dim),
                self.dim + (cell % self.dim),
                2 * self.dim + (cell % (self.dim + 1)),
            ]
        else:
            return [
                math.ceil(cell / self.dim),
                self.dim + (cell % self.dim),
                2 * self.dim + ((cell % self.dim + math.ceil(cell / self.dim) * self.dim) % (self.dim + 1)),
            ]

    def send_to_arduino(self, leds):
        """
        Takes in the three(or really how many ever) integers from 1-96 that correspond
        to values for the 8x12 LED matrix and sends them over serial connection to the
        Arduino using a pre-described protocol

        Returns True if successful, False if error occurred, and throws errors.
        """

        if(len(leds) == 1):
            leds = leds * 3

        if (len(leds) != 3):
            raise ValueError("Function requires 3 or 1 leds")

        anodes = [i%12 if i%12 != 0 else 12 for i in leds]
        cathodes = [i//12+1 if i%12!=0 else i//12 for i in leds]

        sendString = ""
        for anode in anodes:
            if anode < 10:
                sendString += f"0{anode}"
            else:
                sendString += f"{anode}"
        
        for cathode in cathodes:
            if cathode > 8:
                raise ValueError("This format is not compatible with 96 well plate")
            sendString += f"0{cathode}"
        
        try:
            self.arduino.write(sendString.encode())
        except serial.serialutil.SerialException:
            pickle_dump = {'dim':self.dim, 'sampleNum':self.sampleNum}
            pickle_file = open("pool_testing_backup", "wb")
            pickle.dump(pickle_dump, pickle_file)
            pickle_file.close()


            print("Sending data failed! The serial connection was terminated. Recovery data saved to pickle file.")
            sys.exit(0)
        return True
    
    def __init__(self, dim=31, sampleNum=0, readFile=None):
        self.dim = dim
        self.sampleNum = sampleNum
        self.readFile = readFile

        self.setup()


if __name__ == "__main__":
    run = Pool_Matrix()
    while True:
        run.send_to_arduino(run.get_tests())
        run.plus_one()
        time.sleep(3);
