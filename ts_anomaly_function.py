# -*- coding: utf-8 -*-
"""
Created on Fri Nov 29 15:22:42 2019

"""
import torch
from torch import distributions


# %% Outlier detection

# arguments
# - sequence: a tensor with dimensions T x D, where 
#      T is number of obs and D is feature dimensions
# - net: a trained model which outputs 2 params for each feature,
#      that is, a tensor of dimension T x 2*D
# - prob_threshold: a number between 0 and 1. An observation with 
#      probability < prob_threshold is labeled as an outlier
def detect_anomalies(sequence, net, device, prob_threshold):
    with torch.no_grad():
        # get it to the device and put the batch dimension
        prepared_sequence = (sequence).to(device).unsqueeze(0)

        # run the model
        output_model = net(prepared_sequence, device)

        # get parameters of predicted data distribution for all time steps
        mu, logvar = torch.chunk(output_model["params"], 2, dim=-1)
        std_dev = torch.exp(logvar / 2)

        # drop batch dimension, if present (only needed for training)
        mu = mu.squeeze()
        std_dev = std_dev.squeeze()

        # main loop to measure outlier probability
        probs = []
        labels = [False] * mu.shape[0]
        for t in range(0, mu.shape[0] - 1):
            cov_matrix = torch.diag(std_dev[t, :])
            # define distribution with params estimated for time t+1
            # in the original sequence (that's simply t in the params
            # outputted by the model)
            p = distributions.MultivariateNormal(mu[t, :], cov_matrix)

            # measure the probability of the observation at time t+1
            # under the model and store the probability
            probability = torch.exp(p.log_prob(prepared_sequence[0, t + 1, :])).cpu().detach().numpy()
            probs.append(probability)

            # store outlier label
            if probability < prob_threshold:
                labels[t + 1] = True

        # collect results in a dictionary
        outliers = {
            "outlier_label": labels,
            "probability": probs
        }
    return outliers

# %% test outlier detection

## select the sequence to test the network on
# sequence = valid_dataset.get_data()[0]
# prob_threshold = 0.1
#
# foo = detect_anomalies(sequence,net,0.0001)
# plt.plot(foo["probability"])
