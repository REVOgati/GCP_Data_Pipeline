with source_data as (
    select * from {{ source('fwg_raw', 'raw_products') }}
),

renamed as (
    select
        cast(product_id as string) as product_id,
        cast(product_name as string) as product_name,
        cast(category as string) as product_category,
        cast(unit_cost_kes as numeric) as unit_cost_kes,
        cast(unit_price_kes as numeric) as unit_price_kes,
        cast(is_perishable as boolean) as is_perishable,
        cast(is_catch_weight as boolean) as is_catch_weight,
        cast(shelf_life_days as int64) as shelf_life_days
    from source_data
)

select * from renamed