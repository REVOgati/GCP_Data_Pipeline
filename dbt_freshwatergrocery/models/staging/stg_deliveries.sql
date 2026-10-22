with source_data as (
    select * from {{ source('fwg_raw', 'raw_deliveries') }}
),

renamed as (
    select
        cast(delivery_id as string) as delivery_id,
        cast(order_id as string) as order_id,
        cast(rider_id as string) as rider_id,
        cast(dispatch_time as timestamp) as dispatch_time,
        cast(delivered_time as timestamp) as delivered_time,
        cast(delivery_distance_km as numeric) as delivery_distance_km
    from source_data
)

select * from renamed