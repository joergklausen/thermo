# %%
import datetime
import schedule
import time
import thermo.instr.tei49c as tei49c
import thermo.instr.tei49i as tei49i
import thermo.common.configparser as parser

# %%
def main():
    try:
        cfg = parser.read_config("thermo.cfg")

        print(f"Initializing calibrator ...")
        name = cfg["calibrator"]["name"]
        calibrator = tei49c.TEI49C(name=name, config=cfg)
        calibrator.get_config()
        time.sleep(2)
        calibrator.set_config()
        schedule.every(cfg[name]['sampling_interval']).minutes.at(':05').do(calibrator.get_data)

        print(f"Initializing analyzer(s) ...")
        for analyzer in cfg["analyzers"]:
            if analyzer == "tei49i_1":
                tei49i_1 = tei49i.TEI49I(name="tei49i_1", config=cfg)
                tei49i_1.get_config()
                tei49i_1.set_config()
                schedule.every(cfg["tei49i_1"]['sampling_interval']).minutes.at(':10').do(tei49i_1.get_data)

            if analyzer == "tei49i_2":
                tei49i_2 = tei49i.TEI49I(name="tei49i_2", config=cfg)
                tei49i_2.get_config()
                tei49i_2.set_config()
                schedule.every(cfg["tei49i_2"]['sampling_interval']).minutes.at(':15').do(tei49i_2.get_data)

            if analyzer == "tei49i-ps":
                tei49i_ps = tei49i.TEI49I(name="tei49i-ps", config=cfg)
                tei49i_ps.get_config()
                tei49i_ps.set_config()
                schedule.every(cfg["tei49i-ps"]['sampling_interval']).minutes.at(':20').do(tei49i_ps.get_data)

        print(f"# Begin comparison ...")
        schedule.every(cfg["calibrator"]["maintain_level"]).minutes.at(':30').do(calibrator.set_o3_conc)
 
        while True:
            schedule.run_pending()
            time.sleep(1)

    except Exception as err:
        print(err)

if __name__ == "__main__":
    main()
# %%
