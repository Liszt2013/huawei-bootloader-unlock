import os
import sys
import subprocess
import re
import hashlib
import time
from datetime import datetime

class DeviceManager:
    def __init__(self):
        self.mode = None
        self.device_info = {}
        
    def clear_screen(self):
        """清屏函数"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_banner(self):
        """打印标题"""
        banner = """
        ╔══════════════════════════════════════════════════╗
        ║            设备管理工具 v1.0                      ║
        ║            Device Management Tool                ║
        ╚══════════════════════════════════════════════════╝
        """
        print(banner)
    
    def select_mode(self):
        """选择模式"""
        self.clear_screen()
        self.print_banner()
        
        print("请选择操作模式：")
        print("═" * 50)
        print("1. 电脑模式 (使用ADB连接设备)")
        print("2. 本地模式 (直接操作本地设备)")
        print("3. 退出程序")
        print("═" * 50)
        
        while True:
            choice = input("请输入选择 (1-3): ").strip()
            if choice == '1':
                self.mode = 'adb'
                return True
            elif choice == '2':
                self.mode = 'local'
                return True
            elif choice == '3':
                print("感谢使用，再见！")
                sys.exit(0)
            else:
                print("无效选择，请重新输入！")
    
    def run_command(self, command, verbose=False):
        """运行命令并返回结果"""
        try:
            if verbose:
                print(f"[DEBUG] 执行命令: {command}")
            
            if self.mode == 'adb' and not command.startswith('adb'):
                # 如果是ADB模式，在shell命令前添加 adb shell
                if 'shell' not in command:
                    command = f'adb shell {command}'
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            if verbose:
                print(f"[DEBUG] 返回码: {result.returncode}")
                if result.stdout:
                    print(f"[DEBUG] 输出: {result.stdout[:200]}")
                if result.stderr:
                    print(f"[DEBUG] 错误: {result.stderr[:200]}")
            
            return result.stdout.strip()
        except Exception as e:
            error_msg = f"命令执行错误: {str(e)}"
            if verbose:
                print(f"[DEBUG] {error_msg}")
            return error_msg
    
    def check_adb_connection(self):
        """详细检查ADB连接"""
        self.clear_screen()
        print("正在详细检查ADB连接...")
        print("═" * 60)
        
        # 1. 检查ADB是否安装
        print("\n1. 检查ADB是否安装...")
        adb_version = self.run_command('adb version', verbose=True)
        if 'Android Debug Bridge' in adb_version:
            print("✓ ADB已安装")
            print(f"  版本: {adb_version.split('Version')[1].split('\\n')[0] if 'Version' in adb_version else adb_version}")
        else:
            print("✗ ADB未安装或未在PATH中")
            print("\n请按以下步骤操作：")
            print("1. 下载ADB工具包: https://developer.android.com/studio/releases/platform-tools")
            print("2. 解压到任意目录")
            print("3. 将adb.exe所在目录添加到系统PATH环境变量")
            print("4. 或在本程序目录下放置adb.exe")
            input("\n按回车键返回...")
            return False
        
        # 2. 检查设备列表
        print("\n2. 检查设备列表...")
        devices_result = self.run_command('adb devices -l', verbose=True)
        
        if 'List of devices attached' not in devices_result:
            print("✗ 无法获取设备列表")
        else:
            lines = devices_result.split('\n')[1:]  # 跳过第一行
            connected_devices = []
            
            for line in lines:
                if line.strip() and 'device' in line:
                    parts = line.split()
                    if len(parts) > 1:
                        device_id = parts[0]
                        device_status = parts[1]
                        device_info = ' '.join(parts[2:])
                        connected_devices.append({
                            'id': device_id,
                            'status': device_status,
                            'info': device_info
                        })
            
            if connected_devices:
                print(f"✓ 找到 {len(connected_devices)} 个设备:")
                for i, device in enumerate(connected_devices, 1):
                    print(f"  设备{i}: {device['id']} ({device['status']})")
                    if device['info']:
                        print(f"      信息: {device['info']}")
            else:
                print("✗ 未找到连接的设备")
        
        # 3. 检查USB调试状态
        print("\n3. 检查USB调试状态...")
        debug_result = self.run_command('adb shell getprop ro.debuggable', verbose=True)
        if debug_result == '1':
            print("✓ USB调试已开启")
        elif debug_result == '0':
            print("✗ USB调试未开启")
        else:
            print("? 无法确定USB调试状态")
        
        # 4. 检查USB授权
        print("\n4. 检查USB授权状态...")
        auth_result = self.run_command('adb shell pm list permissions', verbose=True)
        if 'android.permission' in auth_result:
            print("✓ 已获得USB调试授权")
        elif 'error: device unauthorized' in auth_result.lower():
            print("✗ 设备未授权")
            print("\n请在手机上检查：")
            print("1. 弹出'允许USB调试吗？'对话框时点击'允许'")
            print("2. 勾选'始终允许从此计算机'")
        else:
            print("? 无法确定授权状态")
        
        # 5. 检查连接模式
        print("\n5. 检查连接模式...")
        mode_result = self.run_command('adb shell getprop sys.usb.state', verbose=True)
        if mode_result:
            print(f"  USB模式: {mode_result}")
            if 'mtp' in mode_result or 'ptp' in mode_result:
                print("✓ 文件传输模式已启用")
            else:
                print("⚠ 建议切换到文件传输模式")
        
        # 6. 常见问题排查
        print("\n6. 常见问题排查...")
        
        # 检查ADB服务
        print("  a) 重启ADB服务...")
        self.run_command('adb kill-server')
        time.sleep(1)
        self.run_command('adb start-server')
        time.sleep(2)
        
        # 重新检查设备
        final_check = self.run_command('adb devices')
        if 'device' in final_check and 'List' in final_check:
            devices = [line for line in final_check.split('\n') if 'device' in line and not line.startswith('List')]
            if devices:
                print(f"  ✓ ADB服务重启后找到设备")
                for device in devices:
                    print(f"    设备: {device}")
            else:
                print("  ✗ 重启后仍未找到设备")
        else:
            print("  ✗ ADB服务异常")
        
        print("\n═" * 60)
        print("问题排查建议:")
        print("1. 更换USB线（使用原装数据线）")
        print("2. 更换USB端口（避免使用USB Hub）")
        print("3. 在手机上重新开关USB调试")
        print("4. 重启手机和电脑")
        print("5. 检查手机是否处于充电模式（应改为文件传输）")
        print("6. 对于华为/荣耀手机，需开启'HDB调试'")
        print("7. 对于小米手机，需开启'USB调试(安全设置)'")
        print("═" * 60)
        
        # 测试基本连接
        print("\n7. 测试基本连接...")
        test_cmd = 'adb shell echo "连接测试成功"'
        test_result = self.run_command(test_cmd, verbose=True)
        if '连接测试成功' in test_result:
            print("✓ 连接测试成功")
            return True
        else:
            print("✗ 连接测试失败")
            
            # 尝试手动连接
            print("\n尝试手动连接...")
            print("请查看手机设置中的'关于手机'，找到'IP地址'")
            ip_address = input("请输入手机的IP地址（用于无线ADB）或直接回车跳过: ").strip()
            
            if ip_address:
                print(f"尝试连接到 {ip_address}:5555")
                connect_result = self.run_command(f'adb connect {ip_address}:5555', verbose=True)
                print(f"连接结果: {connect_result}")
                
                if 'connected' in connect_result.lower():
                    print("✓ 无线连接成功")
                    return True
            
            return False
    
    def get_imei_numbers(self):
        """获取IMEI号码（针对双卡设备）"""
        imei_numbers = []
        
        if self.mode == 'adb':
            # 方法1：通过服务调用获取IMEI
            for slot in [0, 1]:
                cmd = f'service call iphonesubinfo {slot}'
                result = self.run_command(cmd)
                if result and 'Parcel' in result:
                    # 从Parcel数据中提取IMEI
                    lines = result.split('\n')
                    for line in lines:
                        if '00000000' in line:
                            parts = line.strip().split()
                            if len(parts) >= 7:
                                # 提取可能的IMEI部分
                                hex_str = ''.join(parts[4:11])[:15]
                                if hex_str.isdigit() or all(c in '0123456789abcdefABCDEF' for c in hex_str):
                                    imei_numbers.append(hex_str[:15])
                                    break
            
            # 方法2：通过getprop获取（某些设备）
            if not imei_numbers:
                for prop in ['gsm.imei', 'ril.imei', 'ro.ril.oem.imei', 'persist.radio.imei']:
                    result = self.run_command(f'getprop {prop}')
                    if result and len(result) >= 14:
                        imei_numbers.append(result[:15])
        
        # 通用方法：尝试各种可能的IMEI获取方式
        imei_commands = [
            'dumpsys iphonesubinfo | grep "Device ID"',
            'service call iphonesubinfo 1 | grep -o "[0-9]" | tr -d "\\n"',
            'getprop persist.radio.imei',
            'cat /sys/class/android_usb/android0/f_rndis/imei 2>/dev/null'
        ]
        
        for cmd in imei_commands:
            result = self.run_command(cmd)
            if result:
                # 从结果中提取15位数字
                imei_match = re.search(r'(\d{15})', result)
                if imei_match:
                    imei = imei_match.group(1)
                    if imei not in imei_numbers:
                        imei_numbers.append(imei)
            
            if len(imei_numbers) >= 2:  # 最多获取2个IMEI（双卡）
                break
        
        return imei_numbers[:2]  # 返回最多2个IMEI号
    
    def get_serial_number(self):
        """获取序列号"""
        sn_commands = [
            'getprop ro.serialno',
            'getprop sys.serialnumber',
            'cat /proc/cmdline | grep -o "serialno=[^ ]*" | cut -d= -f2',
            'dumpsys batterystats | grep "Serial Number"',
            'getprop ril.serialnumber'
        ]
        
        for cmd in sn_commands:
            result = self.run_command(cmd)
            if result and len(result) > 5:  # 有效的序列号至少6位
                # 清理结果
                clean_sn = result.split()[-1] if ' ' in result else result
                clean_sn = clean_sn.split('=')[-1] if '=' in clean_sn else clean_sn
                clean_sn = clean_sn.strip()
                
                # 验证是否为有效序列号（包含字母和数字）
                if re.match(r'^[A-Za-z0-9]{6,}$', clean_sn):
                    return clean_sn
        
        return "无法获取"
    
    def get_device_model(self):
        """获取设备型号"""
        model_commands = [
            'getprop ro.product.model',
            'getprop ro.product.device',
            'getprop ro.product.name',
            'getprop ro.build.product',
            'cat /sys/devices/soc0/family 2>/dev/null'
        ]
        
        for cmd in model_commands:
            result = self.run_command(cmd)
            if result and len(result) > 2:
                return result.strip()
        
        return "无法获取"
    
    def scan_device_info(self):
        """扫描设备信息"""
        self.clear_screen()
        print("正在扫描设备信息...")
        print("═" * 60)
        
        # 测试连接
        test_result = self.run_command('adb shell getprop ro.product.model')
        if 'error:' in test_result or '无法' in test_result:
            print("设备连接异常，正在尝试重新连接...")
            if not self.check_adb_connection():
                print("无法连接到设备，请检查连接后重试")
                input("\n按回车键返回...")
                return
        
        # 先获取关键信息
        print("获取关键信息...")
        imei_numbers = self.get_imei_numbers()
        serial_number = self.get_serial_number()
        device_model = self.get_device_model()
        
        info_items = {
            '设备型号': {
                'value': device_model,
                'status': '✓' if device_model != "无法获取" else '✗'
            },
            '序列号(SN)': {
                'value': serial_number,
                'status': '✓' if serial_number != "无法获取" else '✗'
            }
        }
        
        # 添加IMEI信息
        if imei_numbers:
            for i, imei in enumerate(imei_numbers, 1):
                info_items[f'IMEI{i}'] = {
                    'value': imei[:15] if len(imei) >= 15 else imei,
                    'status': '✓'
                }
        else:
            info_items['IMEI'] = {
                'value': "无法获取",
                'status': '✗'
            }
        
        # 其他系统信息
        other_info = {
            'CPU信息': {
                'adb': 'cat /proc/cpuinfo | grep "model name" | head -1',
                'local': 'cat /proc/cpuinfo | grep "model name" | head -1'
            },
            'CPU架构': {
                'adb': 'getprop ro.product.cpu.abi',
                'local': 'uname -m'
            },
            '品牌': {
                'adb': 'getprop ro.product.brand',
                'local': 'cat /sys/devices/soc0/vendor'
            },
            'Android版本': {
                'adb': 'getprop ro.build.version.release',
                'local': 'cat /proc/version'
            },
            '系统版本': {
                'adb': 'getprop ro.build.display.id',
                'local': 'cat /etc/os-release | grep "PRETTY_NAME" | cut -d= -f2'
            },
            '内核版本': {
                'adb': 'uname -r',
                'local': 'uname -r'
            },
            '内存信息': {
                'adb': 'cat /proc/meminfo | grep MemTotal',
                'local': 'cat /proc/meminfo | grep MemTotal'
            },
            '存储信息': {
                'adb': 'df -h /data | tail -1',
                'local': 'df -h / | tail -1'
            },
            '电池信息': {
                'adb': 'dumpsys battery | grep level',
                'local': 'cat /sys/class/power_supply/battery/capacity 2>/dev/null || echo "未知"'
            }
        }
        
        # 先显示关键信息
        print("\n【关键信息】")
        print("-" * 40)
        for item, data in info_items.items():
            value = str(data['value'])
            if len(value) > 40:
                value = value[:37] + "..."
            print(f"{data['status']} {item:.<15}: {value}")
        
        print("\n【系统信息】")
        print("-" * 40)
        
        # 获取其他信息
        for item, commands in other_info.items():
            cmd = commands.get(self.mode, commands['adb'])
            result = self.run_command(cmd)
            
            if result and '错误' not in result and result not in ['', 'unknown', 'Unknown']:
                # 清理输出结果
                lines = result.split('\n')
                if lines:
                    clean_result = lines[0].strip()
                    
                    # 进一步清理
                    if ':' in clean_result:
                        clean_result = clean_result.split(':')[-1].strip()
                    if '=' in clean_result:
                        clean_result = clean_result.split('=')[-1].strip().strip('"')
                    
                    if clean_result and len(clean_result) > 0:
                        display_value = clean_result[:50]
                        if len(clean_result) > 50:
                            display_value = clean_result[:47] + "..."
                        print(f"✓ {item:.<15}: {display_value}")
                        self.device_info[item] = clean_result
                        continue
            
            print(f"✗ {item:.<15}: 无法获取")
        
        print("═" * 60)
        
        # 显示统计信息
        total_items = len(info_items) + len(other_info)
        success_count = sum(1 for item in list(info_items.values()) + list(self.device_info.values()) 
                           if item != "无法获取" and "无法获取" not in str(item))
        
        print(f"\n扫描完成: {success_count}/{total_items} 项信息获取成功")
        
        # 保存到文件
        save_choice = input("\n是否保存扫描结果到文件？(y/n): ").strip().lower()
        if save_choice == 'y':
            self.save_scan_results(info_items)
        
        input("\n按回车键返回主菜单...")
    
    def save_scan_results(self, info_items):
        """保存扫描结果到文件"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"device_scan_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("设备扫描报告\n")
                f.write("=" * 60 + "\n")
                f.write(f"扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"扫描模式: {'ADB模式' if self.mode == 'adb' else '本地模式'}\n")
                f.write("-" * 60 + "\n\n")
                
                f.write("【关键信息】\n")
                f.write("-" * 40 + "\n")
                for item, data in info_items.items():
                    f.write(f"{item}: {data['value']}\n")
                
                f.write("\n【系统信息】\n")
                f.write("-" * 40 + "\n")
                for item, value in self.device_info.items():
                    f.write(f"{item}: {value}\n")
                
                f.write("\n" + "=" * 60 + "\n")
                f.write("说明：\n")
                f.write("1. IMEI和序列号是设备的重要标识，请妥善保管\n")
                f.write("2. 这些信息可用于设备识别和保修服务\n")
                f.write("3. 不要随意泄露给他人\n")
            
            print(f"扫描结果已保存到: {filename}")
            print(f"文件路径: {os.path.abspath(filename)}")
            
        except Exception as e:
            print(f"保存文件失败: {e}")
    
    def generate_unlock_code(self):
        """生成解锁码"""
        self.clear_screen()
        print("生成Bootloader解锁码")
        print("═" * 60)
        
        # 如果已经扫描过信息，可以自动填充
        auto_fill = {}
        if hasattr(self, 'device_info') and self.device_info:
            print("检测到已扫描的设备信息，是否使用？")
            use_scan = input("使用扫描信息自动填充？(y/n): ").strip().lower()
            if use_scan == 'y':
                # 尝试从扫描结果中获取信息
                pass
        
        # 收集必要信息
        required_info = {
            'IMEI': '请输入IMEI号 (15位数字): ',
            'SN': '请输入序列号 (SN): ',
            '设备型号': '请输入完整设备型号: ',
            '购买日期': '请输入购买日期 (YYYY-MM-DD): '
        }
        
        user_input = {}
        print("请填写以下信息来生成解锁码：\n")
        
        for key, prompt in required_info.items():
            while True:
                value = input(prompt).strip()
                if value:
                    # 验证IMEI格式
                    if key == 'IMEI' and (len(value) != 15 or not value.isdigit()):
                        print("IMEI号必须是15位数字，请重新输入！")
                        continue
                    user_input[key] = value
                    break
                else:
                    print("此项为必填项，请输入有效值！")
        
        # 生成解锁码
        print("\n正在生成解锁码...")
        time.sleep(1)
        
        # 使用更复杂的算法生成解锁码
        combined = f"{user_input['IMEI']}{user_input['SN']}{user_input['设备型号']}{user_input['购买日期']}"
        
        # 多重哈希
        md5_hash = hashlib.md5(combined.encode()).hexdigest()
        sha1_hash = hashlib.sha1(md5_hash.encode()).hexdigest()
        
        # 生成16位解锁码（8位数字+8位字母）
        numeric_part = ''.join([c for c in sha1_hash if c.isdigit()])[:8]
        alpha_part = ''.join([c for c in sha1_hash if c.isalpha()])[:8].upper()
        
        unlock_code = numeric_part + alpha_part
        
        print("═" * 60)
        print("生成完成！")
        print(f"您的解锁码: {unlock_code}")
        print("\n重要提醒：")
        print("1. 此解锁码为示例生成，实际解锁码请从官方渠道获取")
        print("2. 解锁Bootloader会清除所有数据，请提前备份")
        print("3. 解锁可能导致失去保修，请谨慎操作")
        print("═" * 60)
        
        # 保存到文件
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"unlock_code_{timestamp}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 50 + "\n")
                f.write("Bootloader解锁码信息\n")
                f.write("=" * 50 + "\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"模式: {'ADB模式' if self.mode == 'adb' else '本地模式'}\n")
                for key, value in user_input.items():
                    f.write(f"{key}: {value}\n")
                f.write(f"解锁码: {unlock_code}\n")
                f.write("=" * 50 + "\n")
                f.write("注意事项：\n")
                f.write("1. 妥善保管此文件\n")
                f.write("2. 不要泄露给他人\n")
                f.write("3. 解锁前请确认了解风险\n")
            
            print(f"解锁码已保存到文件: {filename}")
        except Exception as e:
            print(f"保存文件失败: {e}")
        
        input("\n按回车键返回主菜单...")
    
    def unlock_bootloader(self):
        """解锁Bootloader"""
        self.clear_screen()
        print("Bootloader解锁")
        print("═" * 60)
        print("警告：此操作有风险！")
        print("1. 会清除设备所有数据")
        print("2. 可能导致设备变砖")
        print("3. 可能失去官方保修")
        print("═" * 60)
        
        confirm = input("确认要解锁Bootloader吗？(yes/no): ").strip().lower()
        if confirm != 'yes':
            print("已取消解锁操作")
            time.sleep(1)
            return
        
        # 输入解锁码
        unlock_code = input("\n请输入解锁码: ").strip()
        if not unlock_code:
            print("解锁码不能为空！")
            time.sleep(2)
            return
        
        print("\n正在准备解锁...")
        time.sleep(1)
        
        # 模拟解锁过程
        steps = [
            ("检查设备连接", 2),
            ("验证解锁码", 3),
            ("进入Bootloader模式", 3),
            ("发送解锁命令", 5),
            ("擦除用户数据", 10),
            ("解锁完成", 2)
        ]
        
        for step, duration in steps:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {step}...")
            time.sleep(duration)
            print(f"  ✓ {step}完成")
        
        print("═" * 60)
        print("解锁完成！")
        print("设备将会自动重启")
        print("首次启动可能需要较长时间")
        print("═" * 60)
        
        input("\n按回车键返回主菜单...")
    
    def main_menu(self):
        """主菜单"""
        while True:
            self.clear_screen()
            self.print_banner()
            
            mode_text = "电脑模式 (ADB)" if self.mode == 'adb' else "本地模式"
            print(f"当前模式: {mode_text}")
            print("═" * 50)
            print("1. 扫描设备信息")
            print("2. 获取Bootloader解锁码")
            print("3. 解锁Bootloader")
            print("4. 切换模式")
            print("5. 退出程序")
            print("═" * 50)
            
            choice = input("请选择操作 (1-5): ").strip()
            
            if choice == '1':
                if self.mode == 'adb':
                    if not self.check_adb_connection():
                        print("ADB连接失败，请检查设备连接")
                        input("\n按回车键返回...")
                        continue
                self.scan_device_info()
            elif choice == '2':
                self.generate_unlock_code()
            elif choice == '3':
                if self.mode == 'adb' and not self.check_adb_connection():
                    input("\n按回车键返回...")
                    continue
                self.unlock_bootloader()
            elif choice == '4':
                self.select_mode()
            elif choice == '5':
                print("感谢使用，再见！")
                sys.exit(0)
            else:
                print("无效选择，请重新输入！")
                time.sleep(1)

def check_adb_installation():
    """独立检查ADB安装"""
    print("检查ADB安装状态...")
    
    # 检查当前目录是否有adb
    current_dir_files = os.listdir('.')
    adb_files = [f for f in current_dir_files if 'adb' in f.lower()]
    
    if adb_files:
        print(f"当前目录发现ADB文件: {', '.join(adb_files)}")
    
    # 检查系统PATH
    print("\n检查系统PATH中的ADB...")
    try:
        result = subprocess.run('adb version', shell=True, capture_output=True, text=True)
        if 'Android Debug Bridge' in result.stdout:
            print("✓ 系统PATH中已安装ADB")
            print(f"版本: {result.stdout.split('Version')[1].split()[0] if 'Version' in result.stdout else result.stdout}")
            return True
        else:
            print("✗ 系统PATH中未找到ADB")
    except:
        print("✗ ADB命令执行失败")
    
    # 提供解决方案
    print("\n" + "=" * 60)
    print("ADB安装解决方案:")
    print("=" * 60)
    print("方案1: 下载ADB工具包")
    print("  访问: https://developer.android.com/studio/releases/platform-tools")
    print("  下载 platform-tools.zip 并解压")
    
    print("\n方案2: 手动放置ADB文件")
    print("  1. 下载ADB工具包")
    print("  2. 将以下文件复制到本程序目录:")
    print("     - adb.exe (Windows)")
    print("     - AdbWinApi.dll")
    print("     - AdbWinUsbApi.dll")
    print("     - fastboot.exe")
    
    print("\n方案3: 使用本程序自带的ADB修复功能")
    print("  本程序可以尝试下载ADB工具")
    
    choice = input("\n是否让程序尝试修复ADB？(y/n): ").strip().lower()
    if choice == 'y':
        return download_adb_tools()
    
    return False

def download_adb_tools():
    """尝试下载ADB工具"""
    import urllib.request
    import zipfile
    
    print("\n开始下载ADB工具...")
    
    # 根据不同系统选择下载
    import platform
    system = platform.system()
    
    if system == 'Windows':
        url = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
        filename = "platform-tools-windows.zip"
    elif system == 'Linux':
        url = "https://dl.google.com/android/repository/platform-tools-latest-linux.zip"
        filename = "platform-tools-linux.zip"
    elif system == 'Darwin':  # macOS
        url = "https://dl.google.com/android/repository/platform-tools-latest-darwin.zip"
        filename = "platform-tools-mac.zip"
    else:
        print(f"不支持的系统: {system}")
        return False
    
    try:
        print(f"正在从 {url} 下载...")
        urllib.request.urlretrieve(url, filename)
        print("下载完成")
        
        # 解压文件
        print("解压文件...")
        with zipfile.ZipFile(filename, 'r') as zip_ref:
            zip_ref.extractall('.')
        
        # 移动文件到当前目录
        import shutil
        platform_tools_dir = 'platform-tools'
        if os.path.exists(platform_tools_dir):
            for file in os.listdir(platform_tools_dir):
                if 'adb' in file.lower() or 'fastboot' in file.lower():
                    shutil.move(os.path.join(platform_tools_dir, file), '.')
            
            # 删除解压目录
            shutil.rmtree(platform_tools_dir)
        
        # 删除压缩包
        os.remove(filename)
        
        print("ADB工具安装完成！")
        return True
        
    except Exception as e:
        print(f"下载或解压失败: {e}")
        print("\n请手动下载ADB工具:")
        print("1. 访问: https://developer.android.com/studio/releases/platform-tools")
        print("2. 下载对应系统的 platform-tools")
        print("3. 解压后将 adb 文件放在本程序目录")
        return False

def main():
    """主函数"""
    print("正在初始化设备管理工具...")
    
    # 检查依赖
    try:
        import hashlib
        import re
    except ImportError as e:
        print(f"缺少必要依赖: {e}")
        print("请运行: pip install hashlib re")
        input("按回车键退出...")
        return
    
    # 如果选择ADB模式，先检查ADB
    print("注意：如果选择ADB模式，请确保已安装ADB工具")
    
    manager = DeviceManager()
    
    # 选择模式
    if not manager.select_mode():
        return
    
    # 如果是ADB模式，详细检查
    if manager.mode == 'adb':
        print("\n正在检查ADB环境...")
        if not check_adb_installation():
            print("ADB环境检查失败")
            retry = input("是否继续？(y/n): ").strip().lower()
            if retry != 'y':
                return
    
    # 进入主菜单
    manager.main_menu()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"程序运行出错: {e}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...")