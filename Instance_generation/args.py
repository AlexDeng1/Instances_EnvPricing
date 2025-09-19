import argparse

def get_args():
    """ Parser args for the script. """
    parser = argparse.ArgumentParser(description='Runs Env Pricing model...')

    # instance args

    # problem args
    parser.add_argument('-i', '--name_of_instance', type=str, default='k200-v150')

    # travellers' preferences
    parser.add_argument('--mu_veh', type=float, default=1.943)
    parser.add_argument('--mu_access', type=float, default=2.223)
    parser.add_argument('--sd_veh', type=float, default=0.5)
    parser.add_argument('--sd_access', type=float, default=0.5)
    parser.add_argument('--mu_bike', type=float, default=2.845)
    parser.add_argument('--sd_bike', type=float, default=0.5)

    parser.add_argument('--pricing_levels', type=dict, default={0: -2, 1: -1, 2: 0, 3: 1, 4: 2})
    parser.add_argument('--VOM', type=dict, default={0: 0.45, 1: 0.6, 2: 0.75, 3: 0.9})
    # waiting/walking times
    parser.add_argument('--taxi_wt', type=tuple, default=(2, 8))
    parser.add_argument('--pv_parking', type=tuple, default=(2,8))
    parser.add_argument('--wwt_public', type=tuple, default=(2,8))
    # transport fees and costs
    parser.add_argument('--cs_min_fee', type=float, default=0.2)
    parser.add_argument('--taxi_pick_up', type=float, default=5.23)
    parser.add_argument('--taxi_min_fee', type=float, default=2.38)
    parser.add_argument('--public_ticket', type=float, default=4.83)
    parser.add_argument('--parking_fee', type=float, default=5)
    parser.add_argument('--fuel_cost_per_km', type=float, default=0.16)

    parser.add_argument('--data_path', type=str,
                        default="../Input_data/",
                        help='Path to data.')

    parser.add_argument('--num_of_stations', type=int, default=100)
    parser.add_argument('--cus_scale', type=list, default=[2, 3, 4, 5])
    parser.add_argument('--veh_availability', type=list, default=[0.6, 0.75, 0.9])
    parser.add_argument('--veh_loc', type=int, default=0, help='0: density-based loc; 1: random vehicle loc')

    # parallelism args (set to (n-1)-cores)
    # parser.add_argument('--n_procs', type=int, default=4, help='Number of procs for parallel subproblem solving.')

    # optimization parameters
    parser.add_argument('--time_limit', type=int, default=3600, help='Time limit for solver.')
    parser.add_argument('--mipgap', type=float, default=0.005, help='Gap limit for solver.')
    parser.add_argument('--threads', type=int, default=1, help='Number of threads for MIP solver.')

    # print or not
    parser.add_argument('--print', type=bool, default=False, help='Print the process or not')

    args = parser.parse_args()
    return args