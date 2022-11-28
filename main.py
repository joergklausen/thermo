import schedule
from thermo.tei49c import TEI49C as TEI49C

def main():
    print(f"Testing TEI49c DAQ")

    tei49c = TEI49C(name='tei49c', config=cfg, simulate=False)
    tei49c.get_config()
    schedule.every(cfg['tei49c']['sampling_interval']).minutes.at(':00').do(tei49c.get_data)
    schedule.every(6).hours.at(':00').do(tei49c.set_datetime)
    schedule.every(fetch).seconds.do(tei49c.print_o3)


if __name__ == "__main__":
    main()