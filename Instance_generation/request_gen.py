import pandas as pd
import numpy as np
import math
import csv

class Request_generator:
    def __init__(self,
                 css_dict: dict,
                 travellers_df: pd.DataFrame, trips_df: pd.DataFrame,
                 mu_veh: float, sd_veh: float,
                 mu_access: float, sd_access: float,
                 mu_bike: float, sd_bike: float,
                 wwt_public: tuple, taxi_wt: tuple,
                 pv_park: tuple,
                 fuel_cost_per_km: float,
                 seed):
        '''
        :param p:
        :param wwt_min: minimal walking/waiting time of public transit
        :param wwt_max: maximal walking/waiting time of public transit use [wwt_min, wwt_max] to generate random walking/waiting time
        :param seed: different seed values are used to generate varying instances under the same setting
                     (i.e., the same customer numbers and css quantities)
        '''

        self.travellers_df = travellers_df
        self.trips_df = trips_df
        self.css_dict = css_dict

        # value of in-vehicle time
        self.mu_veh = mu_veh
        self.sd_veh = sd_veh

        # value of walking and waiting time
        self.mu_access = mu_access
        self.sd_access = sd_access

        # walking/waiting time of public transit, taxi, private car modes
        self.wwt_public = wwt_public
        self.taxi_wt = taxi_wt
        self.pv_park = pv_park

        # value of bike time
        self.mu_bike = mu_bike
        self.sd_bike = sd_bike

        # self.veh_speed = veh_speed
        # self.pt_speed = 40      # km/h
        # self.bike_speed = 20    # km/h
        self.fuel_cost_per_km = fuel_cost_per_km

        self.seed = seed

        np.random.seed(self.seed)
        vot_veh = list(np.random.lognormal(self.mu_veh, self.sd_veh, len(self.travellers_df)))
        vot_access = list(np.random.lognormal(self.mu_access, self.sd_access, len(self.travellers_df)))
        vot_bike = list(np.random.lognormal(self.mu_bike, self.sd_bike, len(self.travellers_df)))

        self.vot_veh = vot_veh
        self.vot_access = vot_access
        self.vot_bike = vot_bike

    def unit_transfer_to_min(self, duration):
        travel_time_min = 0
        if len(duration.split(' ')) == 2:
            travel_time_min = float(duration.split(' ')[0])
        elif len(duration.split(' ')) == 4:
            travel_time_min = float(duration.split(' ')[0] * 60 + duration.split(' ')[2])
        return travel_time_min

    def cs_customer_generator(self, cs_pick_up_fee: dict, cs_min_fee: float, public_ticket: float,
                              taxi_pick_up: float, taxi_min_fee: float, parking_fee: float, VTT_scaler: float,
                              env_impacts: dict):
        '''
        :param parking_fee:
        :param VTT_scaler:
        :param taxi_pick_up:
        :param taxi_min_fee:
        :param public_ticket:
        :param cs_min_fee:
        :param cs_pick_up_fee:
        :return: dictionary of requests with price-station combinations
        {'traveller id': [(i0, l0), (i0, l1), ...], }
        '''
        Dict_requests = {}

        # generate random walking-and-waiting time for public transport and taxi
        np.random.seed(self.seed)
        wwt_public = list(np.random.uniform(self.wwt_public[0], self.wwt_public[1], len(self.travellers_df)))
        wt_taxi = list(np.random.uniform(self.taxi_wt[0], self.taxi_wt[1], len(self.travellers_df)))
        wt_park = list(np.random.uniform(self.pv_park[0], self.pv_park[1], len(self.travellers_df)))

        req_id = 0
        for i in range(len(self.travellers_df)):
            # traveller_id
            traveller_idx = self.travellers_df.iloc[i]['traveller_id']

            # row id in the pd Dataframe
            df_idx = self.trips_df[self.trips_df['traveller_id'] == traveller_idx].index.tolist()[0]

            # travel times in minutes
            public_time_in_min = self.unit_transfer_to_min(self.trips_df.iloc[df_idx]['public_duration'])
            cs_time_in_min = self.unit_transfer_to_min(self.trips_df.iloc[df_idx]['cs_duration'])
            driving_time_in_min = self.unit_transfer_to_min(self.trips_df.iloc[df_idx]['driving_duration'])
            wt_css_in_min = self.unit_transfer_to_min(self.trips_df.iloc[df_idx]['wt_css_o']) + \
                            self.unit_transfer_to_min(self.trips_df.iloc[df_idx]['wt_css_d'])
            bike_time_in_min = self.unit_transfer_to_min(self.trips_df.iloc[df_idx]['bicycling_duration'])

            # distances in KM
            public_distance = float(self.trips_df.iloc[df_idx]['public_distance'].split(' ')[0])
            cs_distance = float(self.trips_df.iloc[df_idx]['cs_distance'].split(' ')[0])
            driving_distance = float(self.trips_df.iloc[df_idx]['driving_distance'].split(' ')[0])
            bicycling_distance = float(self.trips_df.iloc[df_idx]['bicycling_distance'].split(' ')[0])

            # calculate travel costs for each transport mode
            cs_costs = {}
            for level in cs_pick_up_fee.keys():
                cs_cost_at_level = cs_pick_up_fee[level] + cs_min_fee * cs_time_in_min + \
                                   self.vot_veh[i] / 60 * (cs_time_in_min) * VTT_scaler \
                                   + self.vot_access[i] / 60 * wt_css_in_min * VTT_scaler

                cs_costs[level] = cs_cost_at_level

            # cost of public transit
            public_cost = public_ticket + self.vot_veh[i] / 60 * (public_time_in_min - wwt_public[i]) * VTT_scaler \
                          + self.vot_access[i] / 60 * wwt_public[i] * VTT_scaler

            # cost of taxi
            taxi_cost = taxi_pick_up + driving_time_in_min * taxi_min_fee \
                        + self.vot_veh[i] / 60 * driving_time_in_min * VTT_scaler \
                        + self.vot_access[i] / 60 * wt_taxi[i] * VTT_scaler

            # cost of private car
            pv_cost = parking_fee + driving_distance * self.fuel_cost_per_km \
                      + self.vot_veh[i] / 60 * driving_time_in_min * VTT_scaler \
                      + self.vot_access[i] / 60 * wt_park[i] * VTT_scaler

            bike_cost = bike_time_in_min * self.vot_bike[i] / 60 * VTT_scaler

            highest_pricing_level = -1
            pricing_list = list(cs_pick_up_fee.keys())
            pricing_list.reverse()

            # ids that represent different transport mode
            alt_cost_dict = {0: public_cost, 1: taxi_cost, 2: bike_cost, 3: pv_cost}
            # alt_distance_dict = {0: public_distance, 1: driving_distance, 2: bicycling_distance, 3: driving_distance}

            # generate the minimal cost alternative
            mode_alt = min(alt_cost_dict, key=lambda mode: alt_cost_dict[mode])
            min_travel_cost = alt_cost_dict[mode_alt]

            for level in pricing_list:
                current_level_fee = cs_costs[level]
                if current_level_fee <= min_travel_cost:
                    highest_pricing_level = level
                    print(traveller_idx, 'cs is selected at pricing level', level)
                    break

            if int(highest_pricing_level) >= 0:
                # currently only consider the nearest carsharing station
                # row id in the pd Dataframe
                df_traveller_idx = self.travellers_df[self.travellers_df['traveller_id'] == traveller_idx].index.tolist()[0]
                sta_o = self.css_dict[self.travellers_df.iloc[df_traveller_idx]['css_o']]
                sta_d = self.css_dict[self.travellers_df.iloc[df_traveller_idx]['css_d']]

                # calculation the environmental impact of carsharing mode and the alternative mode
                # (1) co2_eq of carsharing mode
                env_carsharing = cs_distance * env_impacts["carsharing"]
                env_alt = 0
                # the alternative mode is public transport
                if mode_alt == 0:
                    env_alt += public_distance * env_impacts['public transport']
                # the alternative mode is taxi
                elif mode_alt == 1:
                    env_alt += driving_distance * env_impacts['taxi']
                elif mode_alt == 2:
                    env_alt += bicycling_distance * env_impacts['bike']
                else:
                    env_alt += driving_distance * env_impacts['private car']

                # store the request related information: alternative mode, the highest acceptable pricing level
                Dict_requests[req_id] = [traveller_idx, sta_o, sta_d, highest_pricing_level, mode_alt, env_carsharing, env_alt]
                print("Cost of each transport mode")
                print(cs_costs[highest_pricing_level], alt_cost_dict)

                req_id += 1

        return Dict_requests

    def record_request(self, csv_file_path, dict_requests: dict):
        headerList = ['request no.', 'traveller_id', 'sta_o', 'sta_d', 'highest_pl', 'mode_alt', 'env_carsharing', 'env_alt']
        try:
            with open(csv_file_path, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                first_row = next(reader)
                header_present = first_row == headerList
        except FileNotFoundError:
            # If the file does not exist, we'll consider the header not present
            header_present = False
        except StopIteration:
            # If the file is empty, the header is not present
            header_present = False

        # If the header is not present, write the header
        if not header_present:
            with open(csv_file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headerList)  # Write the header first

        # Append the new data
        with open(csv_file_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for request_id in dict_requests.keys():
                current_results = [request_id] + dict_requests[request_id]
                writer.writerow(current_results)  # Append the new data row







