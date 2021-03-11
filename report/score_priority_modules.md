# Scoring Lua Modules

Based on the data analysis results, we found that most values (pagelinks, langlinks, transclusions etc) are highly skewed and it will be hard to identify and list important modules solely relying on these raw values. We identified a rough list of limits to help create a metric for scoring the module importance. The procedure is shown below for the feature `transcluded_in` as an example. The same process is followed for other features too. See code in `get_distribution.py` file.

# Steps to calculate score

## 1. Get limit value

First data is collected and analysed. The distribution is observed and a limit value is approximated. For the example below, after a couple of iteration it was evident that most modules are transcluded in less than 1 million pages. So those modules transcluded in more than 1 million pages may be worth a little more attention than others. So the limit set for the feature `transcluded_in` is 1e6.

<p float="left">
  <img src="/img/trin.png" width="33%" />
  <img src="/img/trin_gr_1e6.png" width="33%" /> 
  <img src="/img/trin_less_1e6.png" width="33%" />
</p>

Note that these values are later normalized by wiki. So `trancluded_in = traincluded_in/(sum of trainscluded_in in this wiki)` to ensure all wikis got equal priority despite their sizes. Then the limits are expressed as percentage instead of raw values, but it is the same idea.

## 2. Modify distribution

Now that we got our limit value it's time to calculate scores. Each feature would be one component of the score. To normalize and turn raw values to scores we modify the original distribution of the features such that the limit we determined is somewhere below `95%`. Originally the limit would be at the 99.999999....th percentile, that way there is no way we can dig out important modules. The result of modifying the distribution is that we give less importance to modules that have _very_ less values (0-10 for most features), and that's okay for us since we are aiming _high_.

We change distribution using the following formula: `feature = feature[feature>limit*multiplier]`. The multiplier is a value `(0,1]` whichever gives the max value for the percentage. Below is the distribution before and after modification.

![](/img/original_trin_dist.png) ![](/img/modified_trin_dist.png)

## 3. Get feature score

To get the score from the feature all we have to do is find what percentile it is in the modified distribution. Is it 99th percentile? Quite important! Is it 5th percentile? Maybe not so important, so has a low score of 0.05. This also ensures that the values across features are standardized to be between 0 and 1.

## 4. Get score

Now to get the score of the module we calculate the weighted sum of the feature scores.

`score = feature_score1 * weight1 + feature_score2 * weight2 + ...`

The weights here are changeable and we can increase or decrease them to get different score (and so list of modules we think are important) based on what features are more important for us to consider.

# Sample scores

Here are some modules with their final scores.

![](/img/scores.png)
