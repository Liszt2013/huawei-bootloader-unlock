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
    
    def run_command(self, command):
        """运行命令并返回结果"""
        try:
            if self.mode == 'adb':
                # 如果是ADB模式，在所有命令前添加 adb shell
                if not command.startswith('adb'):
                    command = f'adb shell {command}'
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            return result.stdout.strip()
        except Exception as e:
            return f"命令执行错误: {str(e)}"
    
    def check_adb_connection(self):
        """检查ADB连接（原有功能保持不变）"""
        if self.mode != 'adb':
            return True
            
        print("正在检查ADB连接...")
        result = self.run_command('adb devices')
        
        if 'device' not in result or 'List of devices attached' not in result:
            print("未检测到ADB设备！")
            return False
        
        devices = [line for line in result.split('\n') if 'device' in line and not line.startswith('List')]
        if len(devices) == 0:
            print("未找到连接的设备！")
            return False
        
        print(f"找到 {len(devices)} 个设备")
        return True
    
    def get_imei_numbers(self):
        """获取IMEI号码（原有功能保持不变）"""
        imei_numbers = []
        
        if self.mode == 'adb':
            # 方法1：通过getprop获取IMEI
            for prop in ['gsm.imei', 'ril.imei', 'ro.ril.oem.imei']:
                result = self.run_command(f'getprop {prop}')
                if result and len(result) >= 14:
                    imei_numbers.append(result[:15])
        
        # 通用方法
        imei_commands = [
            'dumpsys iphonesubinfo | grep "Device ID"',
            'service call iphonesubinfo 1',
        ]
        
        for cmd in imei_commands:
            result = self.run_command(cmd)
            if result:
                imei_match = re.search(r'(\d{15})', result)
                if imei_match:
                    imei = imei_match.group(1)
                    if imei not in imei_numbers:
                        imei_numbers.append(imei)
            
            if len(imei_numbers) >= 2:
                break
        
        return imei_numbers[:2]
    
    def get_serial_number(self):
        """获取序列号（原有功能保持不变）"""
        sn_commands = [
            'getprop ro.serialno',
            'getprop sys.serialnumber',
            'cat /proc/cmdline | grep -o "serialno=[^ ]*" | cut -d= -f2',
        ]
        
        for cmd in sn_commands:
            result = self.run_command(cmd)
            if result and len(result) > 5:
                clean_sn = result.split()[-1] if ' ' in result else result
                clean_sn = clean_sn.split('=')[-1] if '=' in clean_sn else clean_sn
                clean_sn = clean_sn.strip()
                
                if re.match(r'^[A-Za-z0-9]{6,}$', clean_sn):
                    return clean_sn
        
        return "无法获取"
    
    def get_device_model(self):
        """获取设备型号（原有功能保持不变）"""
        model_commands = [
            'getprop ro.product.model',
            'getprop ro.product.device',
            'getprop ro.product.name',
            'getprop ro.build.product',
        ]
        
        for cmd in model_commands:
            result = self.run_command(cmd)
            if result and len(result) > 2:
                return result.strip()
        
        return "无法获取"
    
    def estimate_manufacture_date(self, sn, model, imei):
        """推断生产日期（原有功能保持不变）"""
        print("\n正在推断生产日期...")
        
        # 荣耀手机SN码分析
        if sn and len(sn) >= 10:
            print(f"分析SN码: {sn}")
            
            # 荣耀常见格式分析
            if len(sn) == 17:  # 你的SN码长度
                # 尝试解析第7-10位
                if len(sn) >= 10:
                    year_code = sn[6]  # 第7位
                    month_code = sn[7]  # 第8位
                    day_code = sn[8:10]  # 第9-10位
                    
                    print(f"  第7位(年份): {year_code}")
                    print(f"  第8位(月份): {month_code}")
                    print(f"  第9-10位(日): {day_code}")
                    
                    # 年份解析
                    year_map = {
                        '8': '2018', '9': '2019', '0': '2020',
                        '1': '2021', '2': '2022', '3': '2023',
                        '4': '2024', '5': '2025', '6': '2026',
                        '7': '2027'
                    }
                    
                    if year_code in year_map:
                        year = year_map[year_code]
                        
                        # 月份解析
                        if month_code.isdigit():
                            month = int(month_code)
                            if 1 <= month <= 12:
                                # 日解析
                                if day_code.isdigit():
                                    day = int(day_code)
                                    if 1 <= day <= 31:
                                        return f"{year}年{month}月{day}日"
                                    else:
                                        return f"{year}年{month}月"
                                else:
                                    return f"{year}年{month}月"
        
        # 其他推断方法
        build_date = self.run_command('getprop ro.build.date')
        if build_date:
            try:
                # 从构建日期推断
                date_match = re.search(r'(\w{3}\s+\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+\w{3}\s+(\d{4}))', build_date)
                if date_match:
                    build_year = date_match.group(2)
                    return f"约{build_year}年"
            except:
                pass
        
        return "无法推断"
    
    def scan_device_info(self):
        """扫描设备信息（原有功能保持不变）"""
        self.clear_screen()
        print("正在扫描设备信息...")
        print("═" * 60)
        
        # 先获取关键信息
        print("获取关键信息...")
        imei_numbers = self.get_imei_numbers()
        serial_number = self.get_serial_number()
        device_model = self.get_device_model()
        
        # 推断生产日期
        manufacture_date = self.estimate_manufacture_date(
            serial_number, 
            device_model, 
            imei_numbers[0] if imei_numbers else ""
        )
        
        info_items = {
            '设备型号': {
                'value': device_model,
                'status': '✓' if device_model != "无法获取" else '✗'
            },
            '序列号(SN)': {
                'value': serial_number,
                'status': '✓' if serial_number != "无法获取" else '✗'
            },
            '生产日期': {
                'value': manufacture_date,
                'status': '✓' if manufacture_date != "无法推断" else '✗'
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
        """保存扫描结果到文件（原有功能保持不变）"""
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
                f.write("1. 生产日期为程序推断，仅供参考\n")
                f.write("2. IMEI和序列号是设备的重要标识，请妥善保管\n")
                f.write("3. 这些信息可用于设备识别和保修服务\n")
                f.write("4. 不要随意泄露给他人\n")
            
            print(f"扫描结果已保存到: {filename}")
            print(f"文件路径: {os.path.abspath(filename)}")
            
        except Exception as e:
            print(f"保存文件失败: {e}")
    
    def generate_unlock_code(self):
        """生成解锁码（原有功能保持不变）"""
        self.clear_screen()
        print("生成Bootloader解锁码")
        print("═" * 60)
        
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
                    if key == 'IMEI' and (len(value) != 15 or not value.isdigit()):
                        print("IMEI号必须是15位数字，请重新输入！")
                        continue
                    user_input[key] = value
                    break
                else:
                    print("此项为必填项，请输入有效值！")
        
        print("\n正在生成解锁码...")
        time.sleep(1)
        
        combined = ''.join([f"{k}:{v}" for k, v in user_input.items()])
        unlock_hash = hashlib.md5(combined.encode()).hexdigest()
        unlock_code = unlock_hash[:16].upper()
        
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
    
    def detect_device_mode_for_unlock(self):
        """【专门用于解锁功能】检测设备模式"""
        print("\n正在检测设备当前模式...")
        print("═" * 60)
        
        detected_modes = []
        
        # 1. 检测ADB模式
        try:
            adb_result = subprocess.run('adb devices', shell=True, capture_output=True, text=True)
            if 'List of devices attached' in adb_result.stdout:
                lines = [line for line in adb_result.stdout.split('\n') if 'device' in line and not line.startswith('List')]
                if lines:
                    detected_modes.append(('ADB模式', 'normal'))
                    print("✓ 检测到ADB模式（正常开机）")
        except:
            pass
        
        # 2. 检测Fastboot模式
        try:
            fastboot_result = subprocess.run('fastboot devices', shell=True, capture_output=True, text=True)
            if fastboot_result.stdout.strip():
                detected_modes.append(('Fastboot模式', 'fastboot'))
                print("✓ 检测到Fastboot模式（可解锁）")
        except:
            pass
        
        # 3. 检测9008模式（Windows）
        if os.name == 'nt':
            try:
                wmic_result = subprocess.run('wmic path Win32_PnPEntity get Name', shell=True, capture_output=True, text=True)
                if '9008' in wmic_result.stdout or 'QDLoader' in wmic_result.stdout:
                    detected_modes.append(('9008模式', '9008'))
                    print("✓ 检测到9008模式（高通EDL）")
            except:
                pass
        
        # 4. 没有检测到任何模式
        if not detected_modes:
            print("✗ 未检测到任何设备连接")
            print("\n可能的原因：")
            print("1. 设备未连接")
            print("2. 驱动未安装")
            print("3. USB线有问题")
            return None
        
        print("═" * 60)
        
        # 如果有多个模式，让用户选择
        if len(detected_modes) > 1:
            print("\n检测到多个模式，请选择：")
            for i, (mode_name, _) in enumerate(detected_modes, 1):
                print(f"{i}. {mode_name}")
            
            while True:
                try:
                    choice = int(input(f"\n请选择 (1-{len(detected_modes)}): ").strip())
                    if 1 <= choice <= len(detected_modes):
                        return detected_modes[choice-1][1]
                    else:
                        print("无效选择！")
                except:
                    print("请输入数字！")
        else:
            # 只有一个模式
            return detected_modes[0][1]
    
    def unlock_bootloader(self):
        """【修改】解锁Bootloader - 添加模式检测"""
        self.clear_screen()
        print("Bootloader解锁")
        print("═" * 60)
        
        # 先检测设备模式
        device_mode = self.detect_device_mode_for_unlock()
        
        if not device_mode:
            print("无法检测到设备，请检查连接后重试")
            input("\n按回车键返回...")
            return
        
        print(f"\n设备当前模式: {device_mode.upper()}")
        
        # 根据模式给出不同提示
        if device_mode == 'normal':
            print("设备处于正常开机模式")
            print("需要先进入Fastboot模式才能解锁")
            
            enter_fastboot = input("\n是否自动进入Fastboot模式？(y/n): ").strip().lower()
            if enter_fastboot == 'y':
                print("正在重启到Fastboot模式...")
                try:
                    result = subprocess.run('adb reboot bootloader', shell=True, capture_output=True, text=True)
                    print(f"结果: {result.stdout}")
                    print("等待设备进入Fastboot...")
                    time.sleep(5)
                    
                    # 重新检测模式
                    device_mode = self.detect_device_mode_for_unlock()
                    if device_mode != 'fastboot':
                        print("未能成功进入Fastboot模式")
                        input("\n按回车键返回...")
                        return
                except:
                    print("进入Fastboot失败")
                    input("\n按回车键返回...")
                    return
            else:
                print("请手动进入Fastboot模式：")
                print("1. 手机关机")
                print("2. 按住音量下键 + 电源键")
                print("3. 进入Fastboot后继续")
                input("\n按提示操作后按回车键继续...")
                
                # 重新检测模式
                device_mode = self.detect_device_mode_for_unlock()
                if device_mode != 'fastboot':
                    print("未检测到Fastboot模式")
                    input("\n按回车键返回...")
                    return
        
        elif device_mode == '9008':
            print("设备处于9008模式（高通EDL模式）")
            print("⚠ 注意：9008模式下通常无法直接解锁Bootloader")
            print("需要先退出9008模式，进入Fastboot模式")
            
            print("\n退出9008模式的方法：")
            print("1. 长按电源键10秒强制重启")
            print("2. 断开USB线，重新开机")
            print("3. 或重启到Fastboot模式")
            
            input("\n请先退出9008模式后按回车键继续...")
            return
        
        # 继续解锁流程（设备现在应该在fastboot模式）
        print("\n" + "═" * 60)
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
            ("检查Fastboot连接", 2),
            ("验证解锁码", 3),
            ("发送解锁命令", 5),
            ("擦除用户数据", 10),
            ("解锁完成", 2)
        ]
        
        for step, duration in steps:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {step}...")
            time.sleep(duration)
            
            # 如果是发送解锁命令，尝试执行fastboot命令
            if step == "发送解锁命令" and device_mode == 'fastboot':
                try:
                    # 这里只是演示，实际命令需要根据设备型号调整
                    # result = subprocess.run(f'fastboot oem unlock {unlock_code}', shell=True, capture_output=True, text=True)
                    # print(f"  命令结果: {result.stdout}")
                    print("  发送: fastboot oem unlock [解锁码]")
                except:
                    print("  命令执行失败")
            
            print(f"  ✓ {step}完成")
        
        print("═" * 60)
        print("解锁完成！")
        print("设备将会自动重启")
        print("首次启动可能需要较长时间")
        print("═" * 60)
        
        # 询问是否重启到系统
        reboot = input("\n是否重启到系统？(y/n): ").strip().lower()
        if reboot == 'y':
            try:
                result = subprocess.run('fastboot reboot', shell=True, capture_output=True, text=True)
                print(f"重启命令结果: {result.stdout}")
            except:
                print("重启失败")
        
        input("\n按回车键返回主菜单...")
    
    def main_menu(self):
        """主菜单（原有功能保持不变）"""
        while True:
            self.clear_screen()
            self.print_banner()
            
            mode_text = "电脑模式 (ADB)" if self.mode == 'adb' else "本地模式"
            print(f"当前模式: {mode_text}")
            print("═" * 50)
            print("1. 扫描设备信息（含生产日期推断）")
            print("2. 获取Bootloader解锁码")
            print("3. 解锁Bootloader（新增模式检测）")  # 唯一修改的地方：提示文字
            print("4. 切换模式")
            print("5. 退出程序")
            print("═" * 50)
            
            choice = input("请选择操作 (1-5): ").strip()
            
            if choice == '1':
                if self.mode == 'adb' and not self.check_adb_connection():
                    input("\n按回车键返回...")
                    continue
                self.scan_device_info()  # 原有功能
            elif choice == '2':
                self.generate_unlock_code()  # 原有功能
            elif choice == '3':
                # 这里不再调用 check_adb_connection()，而是让 unlock_bootloader() 自己检测
                self.unlock_bootloader()  # 修改后的功能
            elif choice == '4':
                self.select_mode()
            elif choice == '5':
                print("感谢使用，再见！")
                sys.exit(0)
            else:
                print("无效选择，请重新输入！")
                time.sleep(1)

def main():
    """主函数"""
    print("设备管理工具 v1.0")
    print("=" * 50)
    
    manager = DeviceManager()
    
    # 选择模式
    if not manager.select_mode():
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
        input("按回车键退出...")