#!/bin/bash

# 等待数据库准备就绪
echo "Waiting for database..."
sleep 5

# 检查数据库是否需要初始化
echo "Checking database status..."
python manage.py showmigrations --plan | grep -q "[ ]"
NEEDS_MIGRATION=$?

if [ $NEEDS_MIGRATION -eq 0 ]; then
    echo "Initializing database..."
    
    # 运行数据库迁移
    python manage.py migrate

    # 只在 INIT_TEST_DATA=1 时初始化测试数据
    if [ "$INIT_TEST_DATA" = "1" ]; then
        echo "Initializing test data..."
        python manage.py init_llm_data
    fi
    
    echo "Database initialization completed."
else
    echo "Database already initialized."
fi
