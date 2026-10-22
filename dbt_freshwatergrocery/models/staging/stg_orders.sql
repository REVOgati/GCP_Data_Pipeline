with source_data as (
    select * from {{ source('fwg_raw', 'raw_orders') }}
),

renamed as (
    select
        cast(order_id as string) as order_id,
        cast(customer_id as string) as customer_id,
        cast(delivery_zone as string) as delivery_zone,
        cast(order_timestamp as timestamp) as order_timestamp,
        cast(delivery_slot_type as string) as delivery_slot_type,
        cast(scheduled_window_end as timestamp) as scheduled_window_end,
        cast(order_value_kes as numeric) as order_value_kes,
        lower(trim(cast(order_status as string))) as order_status
    from source_data
)

select * from renamed