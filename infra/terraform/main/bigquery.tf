# BigQuery migration target (#5). Schema mirrors
# migration_pipeline.schema.BIGQUERY_SCHEMA — keep the two in sync.
resource "google_bigquery_dataset" "migration" {
  dataset_id  = var.bq_dataset
  location    = var.bq_location
  description = "Migration target: Ducks Unlimited university chapters"
}

resource "google_bigquery_table" "university_chapters" {
  dataset_id          = google_bigquery_dataset.migration.dataset_id
  table_id            = var.bq_table
  deletion_protection = false

  schema = jsonencode([
    { name = "chapter_id", type = "STRING", mode = "REQUIRED" },
    { name = "chapter_name", type = "STRING", mode = "NULLABLE" },
    { name = "city", type = "STRING", mode = "NULLABLE" },
    { name = "state", type = "STRING", mode = "REQUIRED" },
    { name = "longitude", type = "FLOAT", mode = "NULLABLE" },
    { name = "latitude", type = "FLOAT", mode = "NULLABLE" },
  ])
}
