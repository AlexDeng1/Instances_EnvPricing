import pandas as pd
import numpy as np
import math
import csv
import args
from request_gen import Request_generator
import os

class instance_generator:
    def __init__(self, cs_stations: list,
                 requests_df: pd.DataFrame,
                 num_of_selected_requests: int,
                 num_of_selected_stations: int,
                 num_of_veh: int,
                 seed):

        self.cs_stations = cs_stations     # the ids of carsharing stations set in the beginning
        self.requests_df = requests_df

        self.num_of_selected_stations = num_of_selected_stations
        self.num_of_selected_requests = num_of_selected_requests
        self.num_of_veh = num_of_veh

        self.seed = seed

    def selected_data(self):
        # formalize the data structure of selected css/travellers to "string"
        # otherwise it will cause some incompatible problems of reading indices
        np.random.seed(self.seed)
        print("The carsharing stations:", self.cs_stations)
        selected_cs_stations = list(np.random.choice(self.cs_stations, self.num_of_selected_stations, replace=False))

        full_requests = {css: [] for css in selected_cs_stations}

        for req_id in range(len(self.requests_df)):
            css_o = 'CS'+ str(self.requests_df.iloc[req_id]['sta_o'])
            css_d = 'CS'+ str(self.requests_df.iloc[req_id]['sta_d'])

            if css_o in selected_cs_stations and css_d in selected_cs_stations:
                full_requests[css_o].append(req_id)

        # get the maximal_req_num at all selected stations
        maximal_req_num = 0
        for css in selected_cs_stations:
            req_len = len(full_requests[css])
            maximal_req_num += req_len
        print("The maximal number of request with these stations is: ", maximal_req_num)

        # first: calculate the number of requests (customers) should be selected at each station
        num_of_selection_at_sta = {css: math.floor(len(full_requests[css])/maximal_req_num
                                                   * self.num_of_selected_requests)
                                   for css in selected_cs_stations}
        selected_cus_num = sum(num_of_selection_at_sta.values())
        cus_remain = self.num_of_selected_requests - selected_cus_num

        while cus_remain > 0:
            for css in selected_cs_stations:
                proportional_num = math.ceil(len(full_requests[css])/maximal_req_num *
                                             (self.num_of_selected_requests - selected_cus_num))

                num_of_cus = min(proportional_num, cus_remain)
                num_of_selection_at_sta[css] += num_of_cus
                cus_remain += -num_of_cus
        print("The actual amount of maximal requests at each station:")
        full_requests_amount = {css: len(full_requests[css]) for css in selected_cs_stations}
        print(full_requests_amount)
        print("The number of selected customers at each station: ")
        print(num_of_selection_at_sta)
        # print("total number of selected customers: ", sum(num_of_selection_at_sta.values()))

        # second: randomly select the certain number of requests for each station
        selected_requests_all = []
        dict_selected_requests = {i: 0 for i in selected_cs_stations}

        for css in selected_cs_stations:
            np.random.seed(self.seed)
            selected_requests_sta = list(np.random.choice(full_requests[css], num_of_selection_at_sta[css],
                                                            replace=False))
            # print("selected travellers at station", css, "is: ", selected_requests_sta)
            selected_requests_all += selected_requests_sta
            dict_selected_requests[css] = selected_requests_sta

        self.dict_selected_requests = dict_selected_requests
        self.num_of_cus_at_statioins = num_of_selection_at_sta
        self.selected_css = selected_cs_stations

        return selected_cs_stations, dict_selected_requests, selected_requests_all

    """
    # Set the initial vehicle loactions based on customer density
    """
    def veh_initial_loc_density(self):

        shared_vehicle_for_centralized_choice = list(range(self.num_of_veh))

        # initialize the veh loc dictionaries
        vehicle_initial_loc = {sv: 0 for sv in range(self.num_of_veh)}
        loc_decision = {(sv, css): 0 for sv in range(self.num_of_veh) for css in self.selected_css}

        # INITIAL LOCATION BASED ON DENSITY
        for css in self.selected_css:
            sv_quantity = np.round(
                self.num_of_cus_at_statioins[css] / self.num_of_selected_requests * self.num_of_veh)
            # print(css, sv_quantity, len(shared_vehicle_for_choose))
            np.random.seed(self.seed)
            sv_selected_for_css = np.random.choice(shared_vehicle_for_centralized_choice,
                                                   size=min(int(sv_quantity),
                                                            len(shared_vehicle_for_centralized_choice)),
                                                   replace=False)
            for sv in sv_selected_for_css:
                vehicle_initial_loc[sv] = css
                loc_decision[(sv, css)] = 1
                shared_vehicle_for_centralized_choice.remove(sv)

        while shared_vehicle_for_centralized_choice:
            # if there is remaining vehicles after density-based initial allocation
            # The remaining shared vehicles are allocated to cs stations randomly
            for sv in shared_vehicle_for_centralized_choice:
                np.random.seed(self.seed)
                assigned_css = np.random.choice(self.cs_stations)
                vehicle_initial_loc[sv] = assigned_css
                loc_decision[(sv, assigned_css)] = 1
                shared_vehicle_for_centralized_choice.remove(sv)

        self.vehicle_initial_loc = vehicle_initial_loc
        self.loc_decision = loc_decision

        return vehicle_initial_loc, loc_decision

    # initial vehicle location random case
    def initial_vehicle_loc_random(self):
        vehicle_initial_loc = {sv: 0 for sv in range(self.num_of_veh)}
        loc_decision = {(sv, css): 0 for sv in range(self.num_of_veh) for css in self.selected_css}

        np.random.seed(self.seed)
        selected_css = list(np.random.choice(self.selected_css, self.num_of_veh, replace=True))
        idx = 0
        for sv in range(self.num_of_veh):
            vehicle_initial_loc[sv] = selected_css[idx]
            loc_decision[(sv, selected_css[idx])] = 1
            idx += 1

        self.vehicle_initial_loc = vehicle_initial_loc
        self.loc_decision = loc_decision

        return vehicle_initial_loc, loc_decision


    def record_instance(self, selected_css_list, selected_requests_dict, selected_request_all, veh_initial_loc, type_veh_initial):
        """
        :return: a csv file containing station information, customer request information, vehicle location information
        """
        name_of_instance = "i"+str(self.num_of_selected_stations)+"r"+str(self.num_of_selected_requests)\
                           +"v"+str(self.num_of_veh)+"seed"+str(self.seed) + 'veh_gen'+str(type_veh_initial)

        csv_file_path = "../Instances/" + name_of_instance+".csv"

        # Append the new data
        with open(csv_file_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # write the header line for carsharing station information
            writer.writerow(['stations', 'num_of_requests'])
            for css in selected_css_list:
                writer.writerow([css, len(selected_requests_dict[css])])

            # write the header line for requests
            writer.writerow(['request_id', 'traveller_id', 'sta_o', 'sta_d', 'highest_pl', 'mode_alt'])
            for req_id in selected_request_all:
                traveller_idx = self.requests_df.iloc[req_id]['traveller_id']
                sta_o = self.requests_df.iloc[req_id]['sta_o']
                sta_d = self.requests_df.iloc[req_id]['sta_d']
                hpl = self.requests_df.iloc[req_id]['highest_pl']
                mode_alt = self.requests_df.iloc[req_id]['mode_alt']
                writer.writerow([req_id, traveller_idx, sta_o, sta_d, hpl, mode_alt])

            # write the header line for the vehicles
            writer.writerow(['vehicle_id', 'loc_css'])
            for veh in veh_initial_loc.keys():
                veh_loc = veh_initial_loc[veh]
                writer.writerow([veh, veh_loc])

        return


if __name__ == '__main__':
    args_set = args.get_args()
    generating_request = False

    # read input data
    input_data_path = args_set.data_path
    traveller_df = pd.read_csv(input_data_path + "geo_info_travellers.csv")
    trips_df = pd.read_csv(input_data_path + "trip_info_multi_modes.csv")
    css_distance_df = pd.read_csv(input_data_path + "distances_between_stations.csv")
    css_df = pd.read_csv(input_data_path + "geo_info_css.csv")
    css_dict = {'CS'+str(i): i for i in range(100)}

    # transport modes and their environmental impacts
    transport_modes = {0: "public transport", 1: "taxi", 2: "bike", 3: "private car", 4: "carsharing"}
    env_impacts = {"public transport": 36, "taxi": 226, "bike": 0, "private car": 135, "carsharing": 98}
    level_VOM = 0
    VTT_scaler = 1 / args_set.VOM[level_VOM]  # 0.45 is the value of money
    """
    # generate the set of requests
    # include all travellers that will choose cs mode under at least one pricing level
    """
    if generating_request:
        generating_requests = Request_generator(css_dict, traveller_df, trips_df, args_set.mu_veh, args_set.sd_veh,
                                                args_set.mu_access, args_set.sd_access, args_set.mu_bike, args_set.sd_bike,
                                                args_set.wwt_public, args_set.taxi_wt, args_set.pv_parking,
                                                args_set.fuel_cost_per_km, seed=0)
        Dict_requests = generating_requests.cs_customer_generator(
            args_set.pricing_levels, args_set.cs_min_fee, args_set.public_ticket, args_set.taxi_pick_up,
            args_set.taxi_min_fee, args_set.parking_fee, VTT_scaler, env_impacts)
        generating_requests.record_request(input_data_path + 'request_dataset.csv', Dict_requests)

    requests_df = pd.read_csv(input_data_path + 'request_dataset.csv')

    """
    # generating instances based on
    (1) initial veh location type: 0 - represents a density-based location, 1 -represents a random distribution
    (2) num_of_requests
    (3) num_of_vehicles
    (4) seed
    """
    instance_id = args_set.name_of_instance
    num_stations = 100
    num_requests = int(instance_id.split("-")[0][1:])
    num_vehs = int(instance_id.split("-")[1][1:])
    type_veh_initial = args_set.veh_loc  # 0 for the density-based location, 1 from the random location
    seed = 0

    instance_id_for_store = 'i'+str(num_stations)+'r'+str(num_requests)+'v'+str(num_vehs)+'seed'+str(seed) \
                            + 'veh_gen'+str(type_veh_initial)

    instance_file_path = '../Instances/' + instance_id_for_store + '.csv'
    veh_loc = {}
    if os.path.exists(instance_file_path):
        print("The instance have already be established...")

    else:
        instance = instance_generator(list(css_dict.keys()), requests_df, num_requests, num_stations, num_vehs, seed=seed)
        selected_css, dict_selected_reuqests, selected_requests_all = instance.selected_data()

        if type_veh_initial == 0:
            veh_loc, loc_dec = instance.veh_initial_loc_density()

        elif type_veh_initial == 1:
            veh_loc, loc_dec = instance.initial_vehicle_loc_random()

        instance.record_instance(selected_css, dict_selected_reuqests, selected_requests_all, veh_loc, type_veh_initial)