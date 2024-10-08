import numpy as np
from PIL import Image
#import cv2
import matplotlib.pyplot as plt
import pickle
import time
import random
from pprint import pprint
import statistics
from itertools import combinations, permutations
import pandas as pd
from matplotlib import style
from tabulate import tabulate
import argparse
style.use("ggplot")

class base_station_controller(object):
    def __init__(self, args):
        self.x, self.y = random.choice(args.user_locations)
        self.user_locations = args.user_locations
        self.size = args.size

    def __str__(self):
        return f"{self.x}, {self.y}"

    def network_params(self):
        agent_move = (self.x, self.y)
        if agent_move not in self.user_locations:
            agent_move = random.choice(self.user_locations)
        return agent_move

    def action(self, choice):
        '''
        Gives us 5 total movement options to get to the 5 different locations for. (u1,u2,u3,u4)
        '''
        if choice == 0:  # 0 stands for user u1
            self.move(x=1, y=1)
        elif choice == 1:  # 1 stands for user u2
            self.move(x=1, y=3)
        elif choice == 2:  # 2 stands for user u3
            self.move(x=3, y=2)
        elif choice == 3:  # 3 stands for user u4
            self.move(x=-4, y=-1)
        elif choice == 4:  # 3 stands for user u5
            self.move(x=-2, y=-4)
        elif choice == 5:  # 3 stands for user u4
            self.move(x=-1, y=-2)

    def move(self, x=False, y=False):
        # If no value for x, move randomly
        if not x:
            self.x = random.choice([i[0] for i in self.user_locations])
        else:
            self.x = x

        # If no value for y, move randomly
        if not y:
            self.y = random.choice([i[1] for i in self.user_locations])
        else:
            self.y = y

        # If we base stations is trying to serve a user out of bounds
        if self.x < -10:
            self.x = -10
        elif self.x > self.size + 1:
            self.x = self.size - 1
        if self.y < -10:
            self.y = -10
        elif self.y > self.size + 1:
            self.y = self.size - 1

        agent_move = (self.x, self.y)
        if agent_move not in self.user_locations:
            agent_move = random.choice(self.user_locations)
            self.x, self.y = agent_move
        else:
            self.x = self.x
            self.y = self.y


def initialize_q_table(args):
    if args.start_q_table is None:
        # initialize the q-table#
        q_table = {}
        for j, o in enumerate(permutations(args.user_locations, 6)):  # 6 implying users
            u, v = o[:3], o[3:]
            if j % 6 == 0:
                q_table[((args.base_station), u), ((args.base_station_2), v)] = [[np.random.uniform(-6, 0) for i in range(6)] for i in range(2)]
        '''
        Extending the q_table with other combinations such as base_1 connected to 4 users and base_2 connected to 2 users and vice versa
        '''
        for i in [4,2]:
            q_table = q_table_extension(i, args, q_table)

    else:
        with open(args.start_q_table, "rb") as f:
            q_table = pickle.load(f)
    return q_table

def q_table_extension(x, args, q_table):
    f = []
    for j, o in enumerate(permutations(args.user_locations, 6)):  # 6 implying users
        u, v = o[:x], o[x:]
        v = tuple(sorted(list(v)))
        if v not in f:
            q_table[((args.base_station), u), ((args.base_station_2), v)] = [[np.random.uniform(-6, 0) for i in range(6)] for i in range(2)]
    return q_table

def search_q_table(agent_move, q_table):
    agent_move = ((agent_move[:2]), (agent_move[2:]))
    agent_move_b1, agent_move_b2 = agent_move
    print(agent_move)
    for k in q_table.keys():
        b1,b2 = k
        if agent_move_b1[0] == b1[0] and agent_move_b1[1] in b1[1]:
            if agent_move_b2[0] == b2[0] and agent_move_b2[1] in b2[1]:
                q_key = k
    return q_key

def radius_based_training(args):
    epsilon = 0.9
    episode_rewards = []
    q_table = initialize_q_table(args)
    bs1_users = [(x,y) for x,y in args.user_locations if x>0 and y>0]
    bs2_users = [i for i in args.user_locations if i not in bs1_users]
    for episode in range(args.episodes):
        bs1_player = base_station_controller(args)
        bs2_player = base_station_controller(args)

        if episode % args.show_every == 0:
            #print(f"on #{episode}, epsilon is {epsilon}")
            print(f"{args.show_every} ep mean: {np.mean(episode_rewards[-args.show_every:])}")
            show = True
        else:
            show = False

        episode_reward = 0
        for i in range(200):
            obs = (args.base_station, bs1_player), (args.base_station_2, bs2_player)
            print('OBS {}'.format(i), obs[0], obs[1])
            if np.random.random() > epsilon:
                # GET THE ACTION
                #actions = [np.argmax(i) for i in q_table[(obs[0][0], (obs[0][1].x, obs[0][1].y), obs[1][0], (obs[1][1].x, obs[1][1].y))]]
                print(obs[0][0], obs[0][1].x, obs[0][1].y, obs[1][0], obs[1][1].x, obs[1][1].y)
                if (obs[0][1].x + obs[0][1].y) != (obs[1][1].x + obs[1][1].y):
                    actions = [np.argmax(i) for i in  q_table[(obs[0][0], (obs[0][1].x, obs[0][1].y), obs[1][0], (obs[1][1].x, obs[1][1].y))]]
            else:
                actions = [np.random.randint(0, 5) for i in range(2)]
            print('action taken', actions)
            # Take the action!
            if actions[0] != actions[1]:
                bs1_player.action(actions[0])
                bs2_player.action(actions[1])
                # the logic
                bs1_associated_user = (bs1_player.x, bs1_player.y)
                bs2_associated_user = (bs2_player.x, bs2_player.y)

                if bs1_associated_user in bs2_users or bs2_associated_user in bs1_users:
                    reward = -(args.base_station_penalty[1])
                elif bs1_associated_user in bs1_users and bs2_associated_user in bs2_users:
                    reward = args.base_station_reward

                ## NOW WE KNOW THE REWARD, LET'S CALC YO
                # first we need to obs immediately after the move.
                new_obs = (args.base_station, bs1_player), (args.base_station_2, bs2_player)

                print('New OBS', new_obs[0][0], new_obs[0][1].x, new_obs[0][1].y, new_obs[1][0], new_obs[1][1].x, new_obs[1][1].y)

                q = q_table[(new_obs[0][0], (new_obs[0][1].x, new_obs[0][1].y), new_obs[1][0], (new_obs[1][1].x, new_obs[1][1].y))]
                max_future_q = [np.max(i) for i in q]
                current_q = [q[0][actions[0]],q[1][actions[1]]]

                new_q = []
                if reward == args.base_station_reward:
                    new_q = [args.base_station_reward/2 for _ in [args.base_station, args.base_station_2]]
                else:
                    new_q = [(1 - args.learning_rate) * current_q[i] + args.learning_rate * (reward + args.discount * max_future_q[i]) for i in range(2)]

                for i in range(2):
                    q_table[((obs[0][0], (obs[0][1].x, obs[0][1].y), obs[1][0], (obs[1][1].x, obs[1][1].y)))][i][actions[i]] = new_q[i]

                episode_reward += reward
                if reward == args.base_station_reward or reward == -args.base_station_penalty[1]:
                    break

        # print(episode_reward)
        episode_rewards.append(episode_reward)
        epsilon *= args.epsilon_decay

    moving_avg = np.convolve(episode_rewards, np.ones((args.show_every,)) / args.show_every, mode='valid')

    plt.plot([i for i in range(len(moving_avg))], moving_avg)
    plt.ylabel(f"Reward {args.show_every}ma")
    plt.xlabel("episode #")
    plt.show()

    with open(f"wireless_communication_qtable-{int(time.time())}.pickle", "wb") as f:
        pickle.dump(q_table, f)

def building_network_parameters(users, base_station):
    #distance
    d = [euclidean_distance(i, base_station) for i in users]
    #channel_gain
    h = np.random.rand(len(users))
    #noise(AWGN) and variance
    n = np.random.random(len(users))
    v = [statistics.variance(n)] * len(users)

    #an algorithm to allocate power coefficients based on the channel gain
    average_h = np.mean(h.tolist())
    p = []
    for i in h:
        i_p = np.random.randint(1, 10)
        if i < average_h:
            i_p = i + i_p
        p.append(float(i_p))

    dataset = pd.DataFrame()
    columns_of_interest = ['users', 'distrance to base', 'channel', 'power', 'noise', 'variance']
    users_loc = [str(i) for i in users]
    for i,j in enumerate([users_loc, d, h, p, n, v]):
        dataset = pd.concat([dataset, pd.DataFrame(j, columns=[columns_of_interest[i]])], axis=1)

    return dataset

def euclidean_distance(user, base_station):
    x_u, y_u = user
    x_b, y_b = base_station
    return np.sqrt((x_u-x_b)**2 + (y_u-y_b)**2)

def intra_level_interference(users, current_user):
    I = 0
    for i,u in enumerate(users):
        if u[0] != current_user: #signal to user can't be interference
            I += (1 * u[3] * np.square(np.abs(u[2])))
    return I

def basestation_level_interference(clusters, bp, index_cluster):
    I = 0
    for i,u in enumerate(clusters):
        if i != index_cluster:
            I += intra_level_interference(u, bp, current_user=None)
    return I

def total_transmitted_superposed_signal(users, current_user, sic=False):
    P = 0
    for i,j in enumerate(users):
        if j[0] != current_user:
            P += j[3]
    return P

def initialize_built_network(args, bs):
    clusters = {}
    for i, j in enumerate(bs):
        cluster = building_network_parameters(args.user_locations, j)
        clusters[j] = cluster.values
        #print('Base station', i + 1, j)
        print(tabulate(cluster, headers='keys', tablefmt='psql'))
    return clusters

def decoding_order(users, i_c, i_b, snr, power):
    D = []
    for i,j in enumerate(users):
        numerator = (snr * (i_c + i_b)) + 1
        denominator = snr * (abs(users[2])**2)
        D.append((users[0], (numerator/denominator)))
    D = sorted(D, key=lambda x:x[1])
    return D

def compute_data_rate(bs, clusters, bps, sic=False):
    data_rates = {}
    for curr_cluster in clusters:
        curr_bs = curr_cluster[0]
        for clu in curr_cluster[1]:
            channel_gain, power_coeffient, distance = clu[2], clu[3], clu[1]  # numerator
            # SINR equation numerator
            numerator = 1 * power_coeffient * np.square(np.abs(channel_gain)) #1 signifies the use-bs indicator
            '----------------------------------------------------------------------------------------'
            intra_interference = intra_level_interference(users=curr_cluster[1], current_user=clu[0])

            inter_interference = 0
            for l in clusters:
                if l[0] != curr_bs:
                    inter_interference += intra_level_interference(users=l[1], current_user=clu[0])

            # SINR equation denominator
            denominator = intra_interference + inter_interference + clu[4]**2
            '----------------------------------------------------------------------------------------'
            user_r = np.log2(1 + (numerator / denominator))
            data_rates[(curr_bs, clu[0])] = user_r
           # print('User {} has data rate {}'.format(user[0], user_r))
    return data_rates

#agent takes action of assigning user to base-station
def action_user_base_station_assignment(users, clu):
    us_bs = {}
    for i in range(len(clu)):
        if clu[i][0] not in us_bs:
            us_bs[clu[i][0]] = users[i]
    #example us_bs = {bs_1:1, bs_2:2}
    return us_bs

#agent checks what's the original state of the network
def check_original_user_bs(us_bs, clu):
    us_bs_s = {}
    for u in us_bs:
        for v in clu:
            if us_bs[u] in [i[0] for i in v[1]]:
                us_bs_s[us_bs[u]] = v[0]
                break
    # example us_bs = {1:bs_1, 2:bs_2}
    return us_bs_s

#pass the before(original state) and after state to decide which scenario to implement
def check_scenario(us_bs_s, us_bs):
    us_bs = dict((v,k) for k,v in us_bs.items())
    if us_bs_s == us_bs:
        scenario = 1
    elif len(set(list(us_bs_s.values()))) == 1:
        scenario = 2
    else:
        scenario = 3
    return  scenario


def swap(clu, users, default_settings):
    d, final = [], []
    scenario_1 = False
    scenario_2 = False
    scenario_3 = False
    default_settings = [(k,v) for k,v in default_settings.items()]
    # print('CLU before\n', tabulate(pd.DataFrame(clu), headers='keys', tablefmt='psql'))
    # print(tabulate(pd.DataFrame(default_settings), headers='keys', tablefmt='psql'))

    #print(default_settings)
    step_1 = action_user_base_station_assignment(users=users, clu=clu)
    step_2 = check_original_user_bs(us_bs=step_1, clu=clu)
    scenario = check_scenario(us_bs_s=step_2, us_bs=step_1)

    #scenario 1 (users don't need swapping because they each belong to their respective base stations)
    if scenario == 1:
        scenario_1 = True
        print('SCENARIO 1\n')
        print(step_1)
        print(step_2)
        final = clu

    #scenario 2, all users on one base station
    elif scenario == 2:
        scenario_2 = True
        print('SCENARIO 2\n')
        print(step_1)
        print(step_2)
        for bt in clu:
            bt_users = [i[0] for i in bt[1]]
            if all(i in bt_users for i in list(step_1.values())):
                x = list(step_1.values())
                clu_remainder = remove_user_from_cluster(user=x[-1], c_cluster=bt[1])
                user_removed = x[-1]
                final.append((bt[0], np.array(clu_remainder)))
                break


        for next_bt in clu:
            if next_bt[0] not in [i[0] for i in final]:
                next_user = fecth_user_from_original_network(base=next_bt[0], user=user_removed, network=default_settings)
                cluster_to_append_removed_user = list(next_bt[1])
                cluster_to_append_removed_user.append(next_user)
                final.append((next_bt[0], np.array(cluster_to_append_removed_user)))

    elif scenario == 3:
        print('SCENARIO 3')
        print(step_1)
        print(step_2)
        temp_final = []
        step_2_reversed = dict((v,k) for k,v in step_2.items())
        for o,p in step_2_reversed.items():
            for c in clu:
                if c[0] == o:
                    clu_remainder = remove_user_from_cluster(user=p, c_cluster=c[1])
                    temp_final.append((o, np.array(clu_remainder)))

        for k,v in step_1.items():
            next_user = fecth_user_from_original_network(base=k, user=v, network=default_settings)
            for b in temp_final:
                if k == b[0]:
                    cluster_to_append_swapped_user = list(b[1])
                    cluster_to_append_swapped_user.append(next_user)
                    final.append((k, np.array(cluster_to_append_swapped_user)))

    return final

def fecth_user_from_original_network(base, user, network):
    for i in network:
        if i[0] == base:
            for j in i[1]:
                if j[0] == str(user):
                    user_needed = j
    return user_needed

def remove_user_from_cluster(user, c_cluster):
    retreived_cluster_users = [i for i in c_cluster if i[0] != user]
    return retreived_cluster_users

def reward_function(before_rates, after_rates):
    reward = 0
    for m, n in before_rates.items():
        m_bs, m_user = m
        before_rate = n
        for o, p in after_rates.items():
            o_bs, o_user = o
            after_rate = p
            #print('here', o_user, m_user, before_rate, after_rate)
            if o_user == m_user and after_rate > before_rate:
                reward += 5
            elif o_user == m_user and after_rate < before_rate:
                reward -= 5
            else:
                reward += 0
    return  reward


def noma_based_training(args):
    epsilon = 0.9
    episode_rewards = []
    swapped_clusters = []
    q_table = initialize_q_table(args)
    base_stations = [args.base_station, args.base_station_2]
    base_stations_powers = [100, 120]
    clusters_in_network = initialize_built_network(args, bs=base_stations)

    clu = []
    for i,c in enumerate(clusters_in_network):
        if i == 0:
            c_ = np.array(clusters_in_network[c][:3,:])
        elif i == 1:
            c_ = np.array(clusters_in_network[c][3:,:])
        clu.append((base_stations[i], c_))

    print(clu)
    data_rates = compute_data_rate(bs=base_stations, clusters=clu, bps=base_stations_powers)
    print('\n')
    #pprint(data_rates)
    #q_table_key = None
    for episode in range(args.episodes):
        bs1_player = base_station_controller(args)
        bs2_player = base_station_controller(args)
        if episode % args.show_every == 0:
            #print(f"on #{episode}, epsilon is {epsilon}")
            print(f"{args.show_every} ep mean: {np.mean(episode_rewards[-args.show_every:])}")
            show = True
        else:
            show = False
        #print('Initial\n', clu)
        episode_reward = 0

        for i in range(200):
            obs = (args.base_station, bs1_player), (args.base_station_2, bs2_player)
            agent_move = (obs[0][0], (obs[0][1].x, obs[0][1].y), obs[1][0], (obs[1][1].x, obs[1][1].y))
            print(agent_move)
            if (obs[0][1].x + obs[0][1].y) != (obs[1][1].x + obs[1][1].y):
                q_table_key = search_q_table(agent_move=agent_move, q_table=q_table)
                if np.random.random() > epsilon:
                    # GET THE ACTION, but make sure the
                    print('Q_table \t\t', q_table_key)
                    actions = [np.argmax(i) for i in  q_table[q_table_key]]
                else:
                    actions = [np.random.randint(0, 5) for i in range(2)]

                print('action taken', actions)
                # Take the action!
                if actions[0] != actions[1]:
                    bs1_player.action(actions[0])
                    bs2_player.action(actions[1])
                    # the logic
                    bs1_associated_user = (bs1_player.x, bs1_player.y)
                    bs2_associated_user = (bs2_player.x, bs2_player.y)
                    print(bs1_associated_user, bs2_associated_user)

                    clu = swap(clu=clu, users=(str(bs1_associated_user), str(bs2_associated_user)), default_settings=clusters_in_network)
                    swapped_cluster = ([(i[0], tuple(j[0] for j in i[1])) for i in clu])
                    if swapped_cluster not in swapped_clusters:
                        computed_noma_rates = compute_data_rate(bs=base_stations, clusters=clu, bps=base_stations_powers)
                        swapped_clusters.append(swapped_cluster)
                        reward = reward_function(before_rates=data_rates, after_rates=computed_noma_rates)
                        print('Reward\n', reward)
                        data_rates = computed_noma_rates
                        ## NOW WE KNOW THE REWARD, LET'S CALC YO
                        # first we need to obs immediately after the move.
                        new_obs = (args.base_station, bs1_player), (args.base_station_2, bs2_player)
                        new_agent_move = (new_obs[0][0], (new_obs[0][1].x, new_obs[0][1].y), new_obs[1][0], (new_obs[1][1].x, new_obs[1][1].y))
                        #print('New OBS', new_obs[0][0], new_obs[0][1].x, new_obs[0][1].y, new_obs[1][0], new_obs[1][1].x, new_obs[1][1].y)
                        new_q_table_key = search_q_table(agent_move=new_agent_move, q_table=q_table)
                        q = q_table[new_q_table_key]
                        max_future_q = [np.max(i) for i in q]
                        current_q = [q[0][actions[0]], q[1][actions[1]]]
                        print('current_q', current_q)
                        new_q = []
                        if reward == args.base_station_reward:
                            new_q = [args.base_station_reward/2 for _ in [args.base_station, args.base_station_2]]
                        else:
                            new_q = [(1 - args.learning_rate) * current_q[i] + args.learning_rate * (reward + args.discount * max_future_q[i]) for i in range(2)]

                        for i in range(2):
                            q_table[q_table_key][i][actions[i]] = new_q[i]

                        episode_reward += reward
                        if reward == args.base_station_reward or reward == -args.base_station_penalty[1]:
                            print('reward', reward, args.base_station_reward, 'penalty', args.base_station_penalty[1])
                            break

        # print(episode_reward)
        episode_rewards.append(episode_reward)
        epsilon *= args.epsilon_decay

    moving_avg = np.convolve(episode_rewards, np.ones((args.show_every,)) / args.show_every, mode='valid')

    plt.plot([i for i in range(len(moving_avg))], moving_avg)
    plt.ylabel(f"Reward {args.show_every}ma")
    plt.xlabel("episode #")
    plt.show()

    with open(f"wireless_communication_qtable-{int(time.time())}.pickle", "wb") as f:
        pickle.dump(q_table, f)
def parse_args():
    parser = argparse.ArgumentParser()
#if __name__=='__main__':
    par = argparse.ArgumentParser()
    par.add_argument("--noma", action="store_true", help="Used when you want to use noma-based rewarding")
    par.add_argument("--radius", action="store_true", help="Used when you want to use radius-based rewarding")
    par.add_argument("--size", default=10, type=int, help="max south, north, east and west length of environment")
    par.add_argument("--episodes", default=25000, type=int, help="default number of episodes for training")
    par.add_argument("--base_station_reward", default=30, type=int, help="max reward for the agent")
    par.add_argument("--base_station_penalty", default=[50, 150], type=list, help="ordered per base station")
    par.add_argument("--epsilon_decay", default=0.9998, type=float, help="learning rate")
    par.add_argument("--learning_rate", default=0.1, type=float, help="learning rate e.g. 0.5, 0.2, 0.1")
    par.add_argument("--discount", default=0.95, type=float)
    par.add_argument("--show_every", default=2500, type=int, help="print status of training every aftter")
    #par.add_argument("--downlink", action="store_true", required=True, help="inform the agent, it's a downlink scenario")
    #par.add_argument("--learner_basis", type=str, required=True, help="Is it based on the radius or noma")
    par.add_argument("--downlink", action="store_true", default='', help="inform the agent, it's a downlink scenario")
    par.add_argument( "--learner_basis", type=str, required=False, help="Is it based on the radius or noma")
   # par.add_argument("--downlink", action="store_true", default=object, help="inform the agent, it's a downlink scenario")
    #par.add_argument("--learner_basis", type=str, default="-", help="Is it based on the radius or noma")
    par.add_argument("--base_station", default=(5, 5), type=int, help="base station location in the environment")
    par.add_argument("--base_station_2", default=(-5,-5), type=int, help="base station location in the environment")
    par.add_argument("--start_q_table", default=None, type=bool, help="Existing or non-existent q table")
    par.add_argument("--user_locations", default=[(1, 1), (1, 3), (3, 2), (-4, -1), (-2, -4), (-1, -2)])
    args = par.parse_args()
   # args = parser.parse_args()
    return args
if __name__ == '__main__':
    if parse_args().learner_basis.lower() == 'noma':
        noma_based_training(parse_args())
    elif parse_args().learner_basis.lower() == 'radius':
        radius_based_training(parse_args())