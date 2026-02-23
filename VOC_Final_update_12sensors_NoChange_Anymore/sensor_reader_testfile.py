from sensors.sensor_reader import VOCSensor

def main():
    try:
        sensor = VOCSensor()

        voc, env = sensor.read_sensors()

        print("\n========== VOC READINGS (12 Sensors) ==========")
        if not voc:
            print("⚠️ No VOC data received. Sensors may not be ready.")
        else:
            for k, v in sorted(voc.items()):
                print(f"{k:20s} : {v}")

        print("\n========== ENV READINGS ==========")
        if not env:
            print("⚠️ No ENV data received.")
        else:
            for k, v in env.items():
                print(f"{k:20s} : {v}")

        print("\n========== SUMMARY ==========")
        print(f"Total VOC channels detected : {len(voc)}")
        print(f"Expected VOC channels       : 12")

        if len(voc) != 12:
            print("⚠️ WARNING: Sensor count mismatch!")
        else:
            print("✅ All 12 sensors are active")

    except Exception as e:
        print("\n❌ FATAL ERROR while reading sensors")
        print(str(e))


if __name__ == "__main__":
    main()
