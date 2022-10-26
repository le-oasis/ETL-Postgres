################################################################################
# Import Libraries
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_unixtime, col, to_timestamp
from pyspark.sql.types import DoubleType
import pandas as pd 
################################################################################
# Create spark session
spark = (SparkSession
    .builder
    .getOrCreate()
)
################################################################################

# Extract data from Postgres
################################################################################
# Read CSV Data
print("######################################")
print("READING CSV FILES")
print("######################################")
################################################################################
df_states_ratings = (
    spark.read
    .format("csv")
    .option("header", True)
    .load("/usr/local/spark/resources/data/book-1.csv")
)
################################################################################
df_needs = (
    spark.read
    .format("csv")
    .option("header", True)
    .load("/usr/local/spark/resources/data/book-2.csv")
)
################################################################################
df_sentiment = (
    spark.read
    .format("csv")
    .option("header", True)
    .load("/usr/local/spark/resources/data/book-3.csv")
)
################################################################################
df_voting = (
    spark.read
    .format("csv")
    .option("header", True)
    .load("/usr/local/spark/resources/data/book-4.csv")
)
################################################################################
df_party = (
    spark.read
    .format("csv")
    .option("header", True)
    .load("/usr/local/spark/resources/data/book-5.csv")
)
################################################################################
# Load data
################################################################################
# Load data to Postgres
print("######################################")
print("LOADING POSTGRES TABLES")
print("######################################")
################################################################################
(df_states_ratings.write
    .format("jdbc")
    .option("url", 'jdbc:postgresql://postgres:5432/airflow')
    .option("dbtable", "public.states")
    .option("user", 'airflow')
    .option("password", 'airflow')
    .mode("overwrite")
    .save()
)
################################################################################
(
    df_needs.write
    .format("jdbc")
    .option("url", 'jdbc:postgresql://postgres:5432/airflow')
    .option("dbtable", "public.needs")
    .option("user", 'airflow')
    .option("password", 'airflow')
    .mode("overwrite")
    .save()
)
################################################################################
(
    df_sentiment.write
    .format("jdbc")
    .option("url", 'jdbc:postgresql://postgres:5432/airflow')
    .option("dbtable", "public.sentiment")
    .option("user", 'airflow')
    .option("password", 'airflow')
    .mode("overwrite")
    .save()
)
################################################################################
(
    df_voting.write
    .format("jdbc")
    .option("url", 'jdbc:postgresql://postgres:5432/airflow')
    .option("dbtable", "public.voting")
    .option("user", 'airflow')
    .option("password", 'airflow')
    .mode("overwrite")
    .save()
)
################################################################################
(
    df_party.write
    .format("jdbc")
    .option("url", 'jdbc:postgresql://postgres:5432/airflow')
    .option("dbtable", "public.party")
    .option("user", 'airflow')
    .option("password", 'airflow')
    .mode("overwrite")
    .save()
)
################################################################################