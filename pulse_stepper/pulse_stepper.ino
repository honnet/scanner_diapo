/* firmware for pulse stepper driver.
 * Copyright 2011-2012 Christophe Combelles <ccomb@gorfou.fr>
 * Ce programme est distribué selon les termes de la licence GNU GPL v3
 * voir http://www.gnu.org/licenses/gpl.html
 */

// set arduino pins
#define X_PULSE      11 // port 4 is DEAD !!!                           // TODO dig that
#define X_DIRECTION  8
#define X_ENABLE     6
#define X_ZEROSENSOR 3
#define X_SWITCH     5

#define DEBUG_PRINT  1

#if DEBUG_PRINT
#   define DPln(...)  Serial.println( __VA_ARGS__)
#   define DP(...)    Serial.print( __VA_ARGS__)
#else
#   define DPln(...)
#   define DP(...)
#endif


// global variables
long x           = 0;       // current step position
int steps_by_rev = 400;     // setting of the drive (nb steps/rev)
long speed       = 400;     // default speed (steps/s) max = 32750
int saved_speed  = speed;
int direction    = 1;       // should be 1 or -1
String command   = "";
int nbtours      = 1;
int retries      = 0;
int value        = 0;
int resp;

boolean readSignal(int sensor) {
    value = digitalRead(sensor);
    for (int i = 0; i < 6; i++) {
        delay(2);
        value += digitalRead(sensor);
    }
    if (value <= 5)
        return LOW;
    else
        return HIGH;
}

void searchZero(long initialSpeed, int searchDirection, unsigned long maxSteps) {
    unsigned long steps = 0;
    unsigned long semiperiod;
    // save previous values
    int saved_direction = direction;
    saved_speed = speed;

    // move step by step until the sensor is found
    digitalWrite(X_DIRECTION, boolean(searchDirection+1));
    while (readSignal(X_ZEROSENSOR)==HIGH && steps < maxSteps) {
        semiperiod = (1000000/initialSpeed)/2;
        digitalWrite(X_PULSE, HIGH);
        delayMicroseconds(semiperiod);
        digitalWrite(X_PULSE, LOW);
        delayMicroseconds(semiperiod);
        steps++; // nb of steps moved
    }
}

void moveTo(int target) {
    unsigned long semiperiod;
    DP("moveTo ");
    DP(target, DEC);
    DP(" speed=");
    DPln(speed);
    // choose direction

    if (target == x)
        return;

    if (target > x) {
        digitalWrite(X_DIRECTION, HIGH);
        direction = 1;
    } else {
        digitalWrite(X_DIRECTION, LOW);
        direction = -1;
    }

    // move to target
    semiperiod = 1000000/speed/2;
    for (int i = x; i != target; i += direction) {
        digitalWrite(X_PULSE, HIGH);
        delayMicroseconds(semiperiod-9);
        digitalWrite(X_PULSE, LOW);
        delayMicroseconds(semiperiod-9);
        x += direction;
    }
}

void setup() {
    direction = HIGH;
    pinMode(X_PULSE,     OUTPUT);
    pinMode(X_DIRECTION, OUTPUT);
    pinMode(X_ENABLE,    OUTPUT);
    pinMode(X_ZEROSENSOR, INPUT);
    pinMode(X_SWITCH,     INPUT);

    Serial.begin(115200);
    //digitalWrite(X_DIRECTION, HIGH);
    //digitalWrite(X_ENABLE, HIGH);

    // search zero at speed 400, forward, 800 steps max
    searchZero(400, 1, 2*steps_by_rev);
    DPln("setup terminated");
}

void loop() {

    // wait and read the serial port signal
    while (!Serial.available())
        delay(10);

    command = String("");
    for (int i = Serial.available(); i > 0; i--) {
        command += char(Serial.read());
    }

    // simple move command
    if (command.substring(0,2) == "go") {
        nbtours = command.substring(2, command.length()).toInt();
        // turn N lap
        moveTo(nbtours*steps_by_rev);
        x = 0;
        // send a signal to the python gui
        DPln("command go terminated");
        return;                                                         // == goto loop
    }                                                                   // XXX do we really want to return ?

    // full scan procedure
    if (command.substring(0,2) == "ok" || command.substring(0,2) == "ic") {
        // run twice in case of ICE
        for (int i = 0; i<=1; i++) {
            nbtours = command.substring(2, command.length()).toInt();
            DPln("start procedure");

            // wait for the 2 opto signals
            for (int i = 0; i < 2; i++) {
                resp = LOW;
                while (resp != HIGH) {
                    resp = readSignal(X_SWITCH);
                    Serial.print(String(resp));
                    delay(50);
                }
                resp = HIGH;
                while (resp != LOW) {
                    resp = readSignal(X_SWITCH);
                    Serial.print(String(resp));
                    delay(50);
                }
            }

            // if no ICE, increment to not run just once
            if (command.substring(0,2) == "ok") { i++; }
        }

        // turn N lap
        moveTo(nbtours*steps_by_rev);
        x = 0;

        // send a signal to the python gui
        Serial.println("finished");
    }
}

