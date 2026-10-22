with source_data as (
    select * from {{ source('fwg_raw', 'raw_inventory') }}
),

renamed as (
    select
        cast(batch_id as string) as batch_id,
        cast(product_id as string) as product_id,
        cast(warehouse_id as string) as warehouse_id,
        cast(quantity_on_hand as int64) as quantity_on_hand,
        cast(harvest_date as date) as harvest_date,
        cast(expiry_date as date) as expiry_date,
        cast(spoilage_flag as boolean) as is_spoiled
    from source_data
)

select * from renamed