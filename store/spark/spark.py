from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("Statistics spark server").master("local[*]").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")


spark.stop()
